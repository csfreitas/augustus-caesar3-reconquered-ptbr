from __future__ import annotations

import contextlib
import hashlib
import json
import os
import shutil
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import reconquered_ptbr_native_media as native


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


@contextlib.contextmanager
def campaign_fixture(existing: bool = False):
    with tempfile.TemporaryDirectory(prefix="rc3-") as temporary:
        root = Path(temporary)
        campaign = root / "Reconquered Campaign"
        (campaign / "xmls").mkdir(parents=True)
        baseline = b"<messages/>"
        (campaign / "xmls" / "RC01 Test corrected.xml").write_bytes(baseline)
        (campaign / "Settings.xml").write_bytes(b"settings sentinel")
        (campaign / "save.svx").write_bytes(b"save sentinel")
        (root / "outside.txt").write_bytes(b"external sentinel")
        localization = root / "payload" / "localization"
        audio = root / "payload" / "audio"
        audio.mkdir(parents=True)
        for name in ("locales.xml", "pt-BR/campaign.xml", "pt-BR/messages/RC01 Test.xml",
                     "pt-BR/media/RC01 Test.xml", "pt-BR/empire/RC01 Test.xml"):
            path = localization / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"<test/>" + name.encode())
        (audio / "voice.wav").write_bytes(b"voice")
        (audio / "music.wav").write_bytes(b"music")
        mission = {"id": "RC01", "xml": "RC01 Test corrected.xml", "sha256": digest(baseline)}
        music = {"assets": [{"file": "music.wav", "sha256": digest(b"music")}], "missions": [mission]}
        speech = {"missions": [{"id": "RC01", "xml": mission["xml"],
                  "baseline_sha256": mission["sha256"],
                  "speech": [{"uid": "intro", "file": "voice.wav", "sha256": digest(b"voice")}]}]}
        for name, value in (("music.json", music), ("speech.json", speech)):
            (root / name).write_text(json.dumps(value), encoding="utf-8")
        if existing:
            (campaign / "localization" / "pt-BR").mkdir(parents=True)
            (campaign / "localization" / "locales.xml").write_bytes(b"original locales")
            (campaign / "localization" / "pt-BR" / "campaign.xml").write_bytes(b"original metadata")
        with (patch.object(native, "MUSIC_PLAN_PATH", root / "music.json"),
              patch.object(native, "SPEECH_PLAN_PATH", root / "speech.json"),
              patch.object(native, "PAYLOAD_AUDIO", audio),
              patch.object(native, "PAYLOAD_LOCALIZATION", localization),
              patch.object(native, "EMPIRE_LOCALIZATION_SCENARIOS", {"RC01 Test"})):
            yield root, campaign


class NativeMediaSafetyTest(unittest.TestCase):
    def assert_sentinels(self, root, campaign):
        self.assertEqual((root / "outside.txt").read_bytes(), b"external sentinel")
        self.assertEqual((campaign / "Settings.xml").read_bytes(), b"settings sentinel")
        self.assertEqual((campaign / "save.svx").read_bytes(), b"save sentinel")
        self.assertEqual((campaign / "xmls" / "RC01 Test corrected.xml").read_bytes(), b"<messages/>")

    def assert_originals(self, root, campaign):
        self.assert_sentinels(root, campaign)
        self.assertEqual((campaign / "localization" / "locales.xml").read_bytes(), b"original locales")
        self.assertEqual((campaign / "localization" / "pt-BR" / "campaign.xml").read_bytes(), b"original metadata")
        self.assertFalse((campaign / native.INSTALL_MANIFEST).exists())
        self.assertFalse((campaign / native.PENDING_DIRECTORY).exists())

    def load_manifest(self, campaign):
        return json.loads((campaign / native.INSTALL_MANIFEST).read_text(encoding="utf-8"))

    def assert_installed(self, campaign, manifest):
        for record in manifest["files"]:
            self.assertEqual(native.sha256(campaign / record["relative_path"]), record["installed_sha256"])

    def test_fresh_install_verify_uninstall_and_reinstall(self):
        with campaign_fixture() as (root, campaign):
            for _ in range(2):
                native.install(campaign)
                native.verify(campaign)
                native.uninstall(campaign)
                self.assertFalse((campaign / native.INSTALL_MANIFEST).exists())
                self.assertFalse((campaign / "localization").exists())
                self.assert_sentinels(root, campaign)

    def test_backup_copy_failure_does_not_touch_destinations(self):
        with campaign_fixture(True) as (root, campaign):
            with patch.object(native.shutil, "copy2", side_effect=OSError("injected disk error")):
                with self.assertRaisesRegex(OSError, "injected disk error"):
                    native.install(campaign)
            self.assert_originals(root, campaign)
            native.install(campaign)
            native.uninstall(campaign)
            self.assert_originals(root, campaign)

    def test_partial_copy_is_not_published(self):
        with campaign_fixture(True) as (root, campaign):
            copy = native.shutil.copy2
            count = 0
            def fail_after_bytes(source, destination):
                nonlocal count
                if Path(destination).parent == campaign / "localization" / "pt-BR" / "audio":
                    count += 1
                    if count == 2:
                        Path(destination).write_bytes(b"partial")
                        raise OSError("injected partial copy")
                return copy(source, destination)
            with patch.object(native.shutil, "copy2", side_effect=fail_after_bytes):
                with self.assertRaisesRegex(OSError, "injected partial copy"):
                    native.install(campaign)
            self.assert_originals(root, campaign)
            self.assertFalse((campaign / "localization" / "pt-BR" / "audio").exists())

    def test_apply_failure_rolls_back_and_preserves_user_files(self):
        with campaign_fixture(True) as (root, campaign):
            user_file = campaign / "localization" / "pt-BR" / "user-notes.txt"
            user_file.write_bytes(b"keep me")
            copy = native._copy_verified
            def fail_metadata(source, destination, expected, before):
                if destination == campaign / "localization" / "pt-BR" / "campaign.xml" and expected != digest(b"original metadata"):
                    raise OSError("injected apply failure")
                return copy(source, destination, expected, before)
            with patch.object(native, "_copy_verified", side_effect=fail_metadata):
                with self.assertRaisesRegex(OSError, "injected apply failure"):
                    native.install(campaign)
            self.assert_originals(root, campaign)
            self.assertEqual(user_file.read_bytes(), b"keep me")

    def test_initial_journal_failure_clears_only_empty_reservation(self):
        with campaign_fixture(True) as (root, campaign):
            with patch.object(native, "_write_json", side_effect=OSError("journal write failure")):
                with self.assertRaisesRegex(OSError, "journal write failure"):
                    native.install(campaign)
            self.assert_originals(root, campaign)

    def test_empty_reservation_recovery_and_nonempty_refusal(self):
        with campaign_fixture(True) as (root, campaign):
            pending = campaign / native.PENDING_DIRECTORY
            pending.mkdir()
            unknown = pending / "unknown.txt"
            unknown.write_bytes(b"do not delete")
            with self.assertRaisesRegex(ValueError, "manual recovery"):
                native.recover(campaign)
            self.assertEqual(unknown.read_bytes(), b"do not delete")
            unknown.unlink()
            native.recover(campaign)
            self.assert_originals(root, campaign)

    def test_phase_transition_write_failure_rolls_back(self):
        with campaign_fixture(True) as (root, campaign):
            write = native._write_json
            def fail_transition(path, value):
                if value.get("phase") == "applying":
                    raise OSError("transition write failure")
                return write(path, value)
            with patch.object(native, "_write_json", side_effect=fail_transition):
                with self.assertRaisesRegex(OSError, "transition write failure"):
                    native.install(campaign)
            self.assert_originals(root, campaign)

    def test_final_manifest_write_failure_rolls_back(self):
        with campaign_fixture(True) as (root, campaign):
            write = native._write_json
            def fail_manifest(path, value):
                if path == campaign / native.INSTALL_MANIFEST:
                    raise OSError("manifest write failure")
                return write(path, value)
            with patch.object(native, "_write_json", side_effect=fail_manifest):
                with self.assertRaisesRegex(OSError, "manifest write failure"):
                    native.install(campaign)
            self.assert_originals(root, campaign)

    def test_final_journal_rename_failure_is_recoverable(self):
        with campaign_fixture(True) as (root, campaign):
            rename = Path.rename
            def fail_rename(path, target):
                if path == campaign / native.PENDING_DIRECTORY:
                    raise PermissionError("journal rename denied")
                return rename(path, target)
            with patch.object(Path, "rename", fail_rename):
                with self.assertRaisesRegex(RuntimeError, "Recovery incomplete"):
                    native.install(campaign)
            self.assertTrue((campaign / native.PENDING_DIRECTORY / "transaction.json").is_file())
            native.recover(campaign)
            self.assert_originals(root, campaign)

    def test_interrupted_install_recovery_is_idempotent(self):
        with campaign_fixture(True) as (root, campaign):
            copy = native._copy_verified
            def interrupt(source, destination, expected, before):
                if destination == campaign / "localization" / "pt-BR" / "campaign.xml":
                    raise KeyboardInterrupt("simulated termination")
                return copy(source, destination, expected, before)
            with patch.object(native, "_copy_verified", side_effect=interrupt):
                with self.assertRaises(KeyboardInterrupt):
                    native.install(campaign)
            with self.assertRaisesRegex(ValueError, "pending"):
                native.install(campaign)
            native.recover(campaign)
            self.assert_originals(root, campaign)
            native.install(campaign)
            native.uninstall(campaign)
            self.assert_originals(root, campaign)

    def test_recovery_refuses_changed_user_file_before_any_write(self):
        with campaign_fixture(True) as (root, campaign):
            copy = native._copy_verified
            def interrupt(source, destination, expected, before):
                if destination == campaign / "localization" / "pt-BR" / "campaign.xml":
                    raise KeyboardInterrupt()
                return copy(source, destination, expected, before)
            with patch.object(native, "_copy_verified", side_effect=interrupt):
                with self.assertRaises(KeyboardInterrupt):
                    native.install(campaign)
            locales = campaign / "localization" / "locales.xml"
            locales.write_bytes(b"user edited")
            with self.assertRaisesRegex(ValueError, "User changes"):
                native.recover(campaign)
            self.assertEqual(locales.read_bytes(), b"user edited")
            self.assertTrue((campaign / native.PENDING_DIRECTORY / "transaction.json").is_file())
            self.assert_sentinels(root, campaign)

    def test_uninstall_restore_failure_rolls_back_to_installed_state(self):
        with campaign_fixture(True) as (root, campaign):
            native.install(campaign)
            manifest = self.load_manifest(campaign)
            copy = native._copy_verified
            def fail_restore(source, destination, expected, before):
                if expected == digest(b"original metadata"):
                    raise OSError("restore failure")
                return copy(source, destination, expected, before)
            with patch.object(native, "_copy_verified", side_effect=fail_restore):
                with self.assertRaisesRegex(OSError, "restore failure"):
                    native.uninstall(campaign)
            self.assert_installed(campaign, manifest)
            self.assertFalse((campaign / native.PENDING_DIRECTORY).exists())
            native.verify(campaign)
            native.uninstall(campaign)
            self.assert_originals(root, campaign)

    def test_interrupted_uninstall_can_recover_without_release_payload(self):
        with campaign_fixture(True) as (root, campaign):
            native.install(campaign)
            manifest = self.load_manifest(campaign)
            copy = native._copy_verified
            def interrupt(source, destination, expected, before):
                if expected == digest(b"original metadata"):
                    raise KeyboardInterrupt()
                return copy(source, destination, expected, before)
            with patch.object(native, "_copy_verified", side_effect=interrupt):
                with self.assertRaises(KeyboardInterrupt):
                    native.uninstall(campaign)
            # Remove only synthetic release copies, never campaign/backup files.
            shutil.rmtree(root / "payload")
            native.recover(campaign)
            self.assert_installed(campaign, manifest)
            native.uninstall(campaign)
            self.assert_originals(root, campaign)

    def test_missing_or_changed_backup_refuses_before_uninstall(self):
        for missing in (False, True):
            with self.subTest(missing=missing), campaign_fixture(True) as (root, campaign):
                native.install(campaign)
                manifest = self.load_manifest(campaign)
                original = campaign / manifest["backup_directory"] / "original/localization/pt-BR/campaign.xml"
                if missing:
                    original.unlink()
                else:
                    original.write_bytes(b"corrupt backup")
                with self.assertRaisesRegex(ValueError, "changed or missing"):
                    native.uninstall(campaign)
                self.assert_installed(campaign, manifest)
                self.assertFalse((campaign / native.PENDING_DIRECTORY).exists())
                self.assert_sentinels(root, campaign)

    def test_manifest_rejects_missing_extra_duplicate_and_escaping_paths(self):
        mutations = {
            "empty": lambda m: m.update(files=[]),
            "missing": lambda m: m["files"].pop(),
            "duplicate": lambda m: m["files"].__setitem__(1, m["files"][0].copy()),
            "traversal": lambda m: m["files"][0].update(relative_path="../outside.txt"),
            "absolute": lambda m: m["files"][0].update(relative_path="C:/outside.txt"),
            "backup": lambda m: m.update(backup_directory="../external"),
            "campaign": lambda m: m.update(campaign_directory="different campaign"),
            "counts": lambda m: m.update(localization_files=999),
            "schema": lambda m: m.update(schema_version=1),
            "dirs": lambda m: m.update(created_directories=["xmls"]),
        }
        for name, mutation in mutations.items():
            with self.subTest(name=name), campaign_fixture(True) as (root, campaign):
                native.install(campaign)
                manifest = self.load_manifest(campaign)
                changed = json.loads(json.dumps(manifest))
                mutation(changed)
                (campaign / native.INSTALL_MANIFEST).write_text(json.dumps(changed), encoding="utf-8")
                for action in (native.verify, native.uninstall):
                    with self.assertRaises(ValueError):
                        action(campaign)
                self.assert_installed(campaign, manifest)
                self.assert_sentinels(root, campaign)

    def test_changed_installed_file_refuses_uninstall(self):
        with campaign_fixture(True) as (root, campaign):
            native.install(campaign)
            changed = campaign / "localization" / "pt-BR" / "campaign.xml"
            changed.write_bytes(b"user translation")
            with self.assertRaisesRegex(ValueError, "changed or missing"):
                native.uninstall(campaign)
            self.assertEqual(changed.read_bytes(), b"user translation")
            self.assertFalse((campaign / native.PENDING_DIRECTORY).exists())
            self.assert_sentinels(root, campaign)

    def test_legacy_manifests_refused_without_changes(self):
        for name in native.CONFLICTING_MANIFESTS:
            with self.subTest(name=name), campaign_fixture(True) as (root, campaign):
                (campaign / name).write_bytes(b"legacy")
                with self.assertRaisesRegex(FileExistsError, "original installer"):
                    native.install(campaign)
                self.assert_originals(root, campaign)

    def test_symlink_destination_refuses_without_touching_external_sentinel(self):
        with campaign_fixture() as (root, campaign):
            external = root / "external-localization"
            external.mkdir()
            (external / "sentinel.txt").write_bytes(b"external directory sentinel")
            try:
                (campaign / "localization").symlink_to(external, target_is_directory=True)
            except OSError as error:
                self.skipTest(f"Host does not permit symlinks: {error}")
            with self.assertRaisesRegex(ValueError, "Links/reparse"):
                native.install(campaign)
            self.assertEqual((external / "sentinel.txt").read_bytes(), b"external directory sentinel")
            self.assert_sentinels(root, campaign)

    def test_reparse_point_is_rejected_even_without_symlink_mode(self):
        with campaign_fixture() as (root, campaign):
            lstat = Path.lstat
            target = campaign / "localization"
            class Reparse:
                st_mode = stat.S_IFDIR
                st_file_attributes = 0x400
            def fake_lstat(path, *args, **kwargs):
                return Reparse() if path == target else lstat(path, *args, **kwargs)
            with patch.object(Path, "lstat", fake_lstat):
                with self.assertRaisesRegex(ValueError, "Links/reparse"):
                    native.install(campaign)
            self.assertFalse((campaign / native.PENDING_DIRECTORY).exists())
            self.assert_sentinels(root, campaign)

    @unittest.skipUnless(os.name == "nt", "Windows path limit policy")
    def test_long_path_refused_before_any_campaign_mutation(self):
        with campaign_fixture(True) as (root, campaign):
            # The extra nesting keeps the campaign itself valid, but makes recovery paths too long.
            target = root / ("deep" * 22) / "Reconquered Campaign"
            target.parent.mkdir()
            campaign.rename(target)
            before = {p.relative_to(target).as_posix(): p.read_bytes() for p in target.rglob("*") if p.is_file()}
            with self.assertRaisesRegex(ValueError, "path too long"):
                native.install(target)
            after = {p.relative_to(target).as_posix(): p.read_bytes() for p in target.rglob("*") if p.is_file()}
            self.assertEqual(before, after)
            self.assertFalse((target / native.PENDING_DIRECTORY).exists())
            self.assertFalse((target / native.BACKUP_DIRECTORY).exists())


if __name__ == "__main__":
    unittest.main()
