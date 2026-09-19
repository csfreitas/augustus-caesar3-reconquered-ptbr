#!/usr/bin/env python3
"""Install Reconquered PT-BR using Augustus native localized-media overlays.

This installer copies localization-owned files only. It validates
the public Reconquered baseline, but never edits the campaign's canonical XMLs.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from generate_scenario_aliases import EMPIRE_SCENARIO_ALIASES, SCENARIO_ALIASES
from reconquered_ptbr_media import (
    MUSIC_PLAN_PATH,
    PAYLOAD_AUDIO,
    PAYLOAD_LOCALIZATION,
    SPEECH_PLAN_PATH,
    load_json,
    sha256,
)


INSTALL_MANIFEST = ".reconquered-ptbr-native-media-install.json"
PENDING_DIRECTORY = ".reconquered-ptbr-native-media-pending"
BACKUP_DIRECTORY = ".reconquered-ptbr-native-media-backup"
COMPONENT = "Reconquered PT-BR native localized-media integration"
SCHEMA_VERSION = 2
EMPIRE_LOCALIZATION_SCENARIOS = {
    "RC01 Ostia", "RC02 Brundisium", "RC03 Capua", "RC04 Tarentum",
    "RC05 Tarraco", "RC06 Syracusae", "RC07 Miletus", "RC08 Mediolanum",
    "RC09 Lugdunum", "RC10 Carthago", "RC11 Tarsus", "RC12 Tingis",
    "RC13 Valencia", "RC14 Lutetia", "RC15 Caesarea", "RC16 Damascus",
    "RC17 Londinium", "RC18 Sarmizegetusa", "RC19 Lindum", "RC20 Massilia",
} | set(EMPIRE_SCENARIO_ALIASES.values())
CONFLICTING_MANIFESTS = (
    ".reconquered-ptbr-media-install.json",
    ".reconquered-ptbr-music-install.json",
    ".reconquered-ptbr-install.json",
)


def build_context() -> tuple[dict, dict, dict[str, dict], dict[str, str]]:
    music_plan = load_json(MUSIC_PLAN_PATH)
    speech_plan = load_json(SPEECH_PLAN_PATH)
    speech_by_mission = {item["id"]: item for item in speech_plan["missions"]}
    audio_hashes = {item["file"]: item["sha256"] for item in music_plan["assets"]}
    if len(speech_by_mission) != len(speech_plan["missions"]) or (
        len({item["id"] for item in music_plan["missions"]}) != len(music_plan["missions"])
    ):
        raise ValueError("Duplicate mission in media plans")
    if len(audio_hashes) != len(music_plan["assets"]):
        raise ValueError("Duplicate music asset in media plan")
    for mission in music_plan["missions"] + speech_plan["missions"]:
        _filename(mission["xml"])
    for asset in music_plan["assets"]:
        _filename(asset["file"])
    for mission in speech_plan["missions"]:
        for asset in mission["speech"]:
            _filename(asset["file"])
    return music_plan, speech_plan, speech_by_mission, audio_hashes


def expected_localization_paths(music_plan: dict) -> set[str]:
    stems = {mission["xml"].removesuffix(" corrected.xml") for mission in music_plan["missions"]}
    stems.update({alias for source, alias in SCENARIO_ALIASES.items() if source in stems})
    messages = {f"pt-BR/messages/{stem}.xml" for stem in stems}
    media = {f"pt-BR/media/{stem}.xml" for stem in stems}
    empire = {f"pt-BR/empire/{stem}.xml" for stem in EMPIRE_LOCALIZATION_SCENARIOS}
    return {"locales.xml", "pt-BR/campaign.xml"} | messages | media | empire


def validate_payload(campaign: Path) -> tuple[dict, dict[str, Path], dict[str, str]]:
    music_plan, speech_plan, speech_by_mission, audio_hashes = build_context()
    _not_link(PAYLOAD_LOCALIZATION)
    _not_link(PAYLOAD_AUDIO)
    localization_files = {}
    for path in PAYLOAD_LOCALIZATION.rglob("*"):
        relative = path.relative_to(PAYLOAD_LOCALIZATION).as_posix()
        _safe_path(PAYLOAD_LOCALIZATION, relative)
        if path.is_file():
            localization_files[relative] = path
    expected_localization = expected_localization_paths(music_plan)
    if set(localization_files) != expected_localization:
        missing = sorted(expected_localization - set(localization_files))
        unexpected = sorted(set(localization_files) - expected_localization)
        raise ValueError(
            f"Invalid native localization payload; missing={missing}, unexpected={unexpected}"
        )

    for mission in music_plan["missions"]:
        speech_mission = speech_by_mission.get(mission["id"])
        if not speech_mission:
            raise ValueError(f"Missing speech plan for {mission['id']}")
        if (
            speech_mission["xml"] != mission["xml"]
            or speech_mission["baseline_sha256"] != mission["sha256"]
        ):
            raise ValueError(f"Media plans disagree for {mission['id']}")
        xml_path = _safe_path(campaign, "xmls/" + mission["xml"])
        if not xml_path.is_file():
            raise FileNotFoundError(f"Missing XML: {mission['xml']}")
        actual = sha256(xml_path)
        if actual != mission["sha256"]:
            raise ValueError(
                f"Incompatible baseline for {mission['xml']}: "
                f"expected {mission['sha256']}, found {actual}"
            )
        for speech in speech_mission["speech"]:
            previous = audio_hashes.get(speech["file"])
            if previous and previous != speech["sha256"]:
                raise ValueError(f"Conflicting audio hash for {speech['file']}")
            audio_hashes[speech["file"]] = speech["sha256"]

    for name, expected_hash in audio_hashes.items():
        source = _safe_path(PAYLOAD_AUDIO, name)
        if not source.is_file():
            raise FileNotFoundError(f"Missing payload audio: {name}")
        actual = sha256(source)
        if actual != expected_hash:
            raise ValueError(
                f"Payload hash mismatch for {name}: expected {expected_hash}, found {actual}"
            )
    return speech_plan, localization_files, audio_hashes


def _filename(value: str) -> str:
    if not isinstance(value, str) or not value or value in (".", "..") or (
        value[-1:] in (".", " ") or re.search(r'[\\/:<>"|?*\x00-\x1f]', value)
    ) or value.split(".")[0].upper() in {
        "CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)),
        *(f"LPT{i}" for i in range(1, 10)),
    }:
        raise ValueError(f"Unsafe file name: {value!r}")
    return value


def _not_link(path: Path) -> None:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return
    if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
        raise ValueError(f"Links/reparse points are not supported: {path}")


def _safe_path(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative:
        raise ValueError("A nonempty relative path is required")
    _not_link(root)
    path = root
    for part in relative.split("/"):
        path /= _filename(part)
        _not_link(path)
    # Leave room for the adjacent atomic-copy temporary file. No registry changes.
    if os.name == "nt" and len(str(path.absolute())) + 20 >= 248:
        raise ValueError(f"Windows path too long; use a shorter campaign/package directory: {path}")
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Path escapes its root: {relative}")
    return path


def _campaign(value: Path) -> Path:
    path = Path(value).expanduser().absolute()
    _not_link(path)
    path = path.resolve(strict=True)
    if path.name != "Reconquered Campaign" or not path.is_dir():
        raise ValueError("The campaign directory must be named exactly 'Reconquered Campaign'.")
    return path


def _file_hash(path: Path) -> str | None:
    _not_link(path)
    if not path.exists():
        return None
    if not path.is_file():
        raise ValueError(f"Expected a regular file: {path}")
    return sha256(path)


def _assert_hash(path: Path, expected: str | None) -> None:
    if _file_hash(path) != expected:
        raise ValueError(f"File changed or missing; refusing to overwrite/remove: {path}")


def _write_json(path: Path, value: dict) -> None:
    # Called only in an exclusively reserved transaction/backup, or under its lock.
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", prefix=".rc3-", suffix=".tmp",
                                     dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        try:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        except BaseException:
            handle.close()
            temporary.unlink(missing_ok=True)
            raise
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _copy_verified(source: Path, destination: Path, expected: str, before: str | None) -> None:
    _assert_hash(source, expected)
    _assert_hash(destination, before)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix=".rc3-", suffix=".tmp", dir=destination.parent,
                                     delete=False) as handle:
        temporary = Path(handle.name)
    try:
        shutil.copy2(source, temporary)
        _assert_hash(temporary, expected)
        with temporary.open("r+b") as handle:
            os.fsync(handle.fileno())
        _assert_hash(destination, before)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def _expected_records() -> tuple[dict[str, str], dict, dict[str, str]]:
    music, speech, _, audio = build_context()
    for mission in speech["missions"]:
        for item in mission["speech"]:
            if item["file"] in audio and audio[item["file"]] != item["sha256"]:
                raise ValueError("Conflicting audio hashes")
            audio[item["file"]] = item["sha256"]
    expected = {"localization/" + path: "localization" for path in expected_localization_paths(music)}
    expected.update({"localization/pt-BR/audio/" + name: "audio" for name in audio})
    counts = {"missions": len(speech["missions"]), "localization_files": len(expected) - len(audio),
              "speech_files": sum(len(item["speech"]) for item in speech["missions"]),
              "music_files": len(music["assets"])}
    return expected, counts, audio


def _validate_manifest(campaign: Path, manifest: dict) -> Path:
    if not isinstance(manifest, dict) or manifest.get("schema_version") != SCHEMA_VERSION or (
        manifest.get("component") != COMPONENT
        or manifest.get("installer") != "portable-python-native-media"
        or manifest.get("campaign_directory") != str(campaign)
    ):
        raise ValueError("Unsupported manifest or different campaign; use the original installer for older releases")
    backup = manifest.get("backup_directory", "")
    if not isinstance(backup, str) or not re.fullmatch(
        re.escape(BACKUP_DIRECTORY) + r"/\d{8}-\d{6}-[0-9a-f]{8}", backup
    ):
        raise ValueError("Invalid backup directory in manifest")
    backup_root = _safe_path(campaign, backup)
    expected, counts, audio = _expected_records()
    if any(type(manifest.get(key)) is not int or manifest[key] != value for key, value in counts.items()):
        raise ValueError("Invalid manifest counts")
    records = manifest.get("files")
    if not isinstance(records, list) or len(records) != len(expected):
        raise ValueError("Manifest does not contain the complete owned file set")
    seen = set()
    permitted_directories = set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Invalid manifest record")
        relative = record.get("relative_path")
        if not isinstance(relative, str) or relative not in expected or relative in seen:
            raise ValueError("Unexpected/duplicate manifest file path")
        seen.add(relative)
        if record.get("kind") != expected[relative] or type(record.get("had_original")) is not bool:
            raise ValueError("Invalid manifest file ownership")
        for field in ("installed_sha256", "original_sha256"):
            value = record.get(field)
            if field == "original_sha256" and not record["had_original"] and value is None:
                continue
            if not isinstance(value, str) or not re.fullmatch(r"[0-9A-F]{64}", value):
                raise ValueError("Invalid manifest hash")
        if not record["had_original"] and record.get("original_sha256") is not None:
            raise ValueError("Unexpected original hash")
        if record["kind"] == "audio" and record["installed_sha256"] != audio[Path(relative).name]:
            raise ValueError("Manifest audio hash differs from release")
        _safe_path(campaign, relative)
        _safe_path(backup_root, "original/" + relative)
        _safe_path(backup_root, "payload/" + relative)
        permitted_directories.update(parent.as_posix() for parent in Path(relative).parents if parent != Path("."))
    directories = manifest.get("created_directories")
    if not isinstance(directories, list) or any(not isinstance(item, str) for item in directories) or (
        len(set(directories)) != len(directories) or not set(directories) <= permitted_directories
    ):
        raise ValueError("Invalid created-directory list")
    return backup_root


def _no_pending(campaign: Path) -> None:
    if _safe_path(campaign, PENDING_DIRECTORY).exists():
        raise ValueError("A transaction is pending. Do not retry installation; run 'recover' first.")


def _load_manifest(campaign: Path) -> tuple[dict, Path]:
    path = _safe_path(campaign, INSTALL_MANIFEST)
    if not path.is_file():
        raise FileNotFoundError("Native installation manifest not found; RC2 requires its original uninstaller")
    manifest = load_json(path)
    return manifest, _validate_manifest(campaign, manifest)


def _validate_backups(campaign: Path, manifest: dict, backup_root: Path) -> None:
    for record in manifest["files"]:
        relative = record["relative_path"]
        _assert_hash(_safe_path(backup_root, "payload/" + relative), record["installed_sha256"])
        if record["had_original"]:
            _assert_hash(_safe_path(backup_root, "original/" + relative), record["original_sha256"])


def _remove_created_directories(campaign: Path, manifest: dict) -> None:
    for relative in sorted(manifest["created_directories"], key=lambda item: item.count("/"), reverse=True):
        path = _safe_path(campaign, relative)
        try:
            path.rmdir()  # Only directories recorded as newly created; never recursive deletion.
        except (FileNotFoundError, OSError):
            pass  # Nonempty directories may now contain user files and must be retained.


def _finish_journal(campaign: Path, manifest: dict) -> None:
    pending = _safe_path(campaign, PENDING_DIRECTORY)
    if {path.name for path in pending.iterdir()} != {"transaction.json"}:
        raise ValueError("Unexpected files in pending directory; retain it for manual recovery")
    backup_root = _safe_path(campaign, manifest["backup_directory"])
    backup_root.mkdir(parents=True, exist_ok=True)
    archived = _safe_path(backup_root, "journal-" + uuid4().hex[:8])
    pending.rename(archived)  # One atomic operation; never leave a lock without its journal.


def _rollback(campaign: Path, journal: dict) -> None:
    manifest = journal["manifest"]
    backup_root = _validate_manifest(campaign, manifest)
    operation = journal.get("operation")
    phase = journal.get("phase")
    if operation not in ("install", "uninstall") or phase not in ("preparing", "applying"):
        raise ValueError("Invalid pending transaction; keep its files for manual recovery")
    if phase == "preparing":
        # No destination has been touched. Staging/backups are intentionally retained.
        _finish_journal(campaign, manifest)
        return
    _validate_backups(campaign, manifest, backup_root)
    # Validate every destination before changing any of them. Unexpected edits stop recovery.
    for record in manifest["files"]:
        current = _file_hash(_safe_path(campaign, record["relative_path"]))
        if current not in (record["installed_sha256"], record["original_sha256"]):
            raise ValueError("User changes detected; keep the pending transaction and backups for manual recovery")
    manifest_path = _safe_path(campaign, INSTALL_MANIFEST)
    if manifest_path.exists() and load_json(manifest_path) != manifest:
        raise ValueError("Installation manifest changed; refusing recovery")
    for record in reversed(manifest["files"]):
        relative = record["relative_path"]
        destination = _safe_path(campaign, relative)
        current = _file_hash(destination)
        target_hash = record["original_sha256"] if operation == "install" else record["installed_sha256"]
        if current == target_hash:
            continue
        if target_hash is None:
            _assert_hash(destination, record["installed_sha256"])
            destination.unlink()
        else:
            folder = "original/" if operation == "install" else "payload/"
            _copy_verified(_safe_path(backup_root, folder + relative), destination, target_hash, current)
    if operation == "install":
        if manifest_path.exists():
            manifest_path.unlink()
        _remove_created_directories(campaign, manifest)
    else:
        _write_json(manifest_path, manifest)
    _finish_journal(campaign, manifest)


def recover(campaign: Path) -> None:
    campaign = _campaign(campaign)
    pending = _safe_path(campaign, PENDING_DIRECTORY)
    journal_path = _safe_path(pending, "transaction.json")
    if not journal_path.is_file():
        if pending.is_dir() and not any(pending.iterdir()):
            # Initial reservation interrupted before the first journal write.
            # No destination is ever touched before that write succeeds.
            pending.rmdir()
            print("Cleared an empty initial reservation; no game files were changed.")
            return
        raise ValueError("No readable pending journal; retain backups and request manual recovery")
    _rollback(campaign, load_json(journal_path))
    print("Recovered the previous state; backups retained. You may retry the operation.")


def _failed_transaction(campaign: Path, journal: dict) -> None:
    try:
        _rollback(campaign, journal)
    except Exception as recovery_error:
        raise RuntimeError("Recovery incomplete; no further changes attempted. Keep backups and run 'recover'.") from recovery_error


def install(campaign: Path) -> None:
    campaign = _campaign(campaign)
    _no_pending(campaign)
    manifest_path = _safe_path(campaign, INSTALL_MANIFEST)
    if manifest_path.exists():
        raise FileExistsError("The native integration is already registered; verify or uninstall it first.")
    for conflicting in CONFLICTING_MANIFESTS:
        if _safe_path(campaign, conflicting).exists():
            raise FileExistsError(f"Remove {conflicting} using its original installer before native installation.")
    _, localization, audio = validate_payload(campaign)
    sources = {"localization/" + relative: path for relative, path in localization.items()}
    sources.update({"localization/pt-BR/audio/" + name: _safe_path(PAYLOAD_AUDIO, name) for name in audio})
    expected, counts, _ = _expected_records()
    backup_relative = BACKUP_DIRECTORY + "/" + datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid4().hex[:8]
    records = []
    created_directories = set()
    for relative, source in sorted(sources.items()):
        destination = _safe_path(campaign, relative)
        original_hash = _file_hash(destination)
        records.append({"kind": expected[relative], "relative_path": relative,
                        "had_original": original_hash is not None, "original_sha256": original_hash,
                        "installed_sha256": sha256(source)})
        parent = destination.parent
        while parent != campaign and not parent.exists():
            created_directories.add(parent.relative_to(campaign).as_posix())
            parent = parent.parent
    manifest = {"schema_version": SCHEMA_VERSION, "component": COMPONENT,
                "installer": "portable-python-native-media", "installed_utc": datetime.now(timezone.utc).isoformat(),
                "campaign_directory": str(campaign), "backup_directory": backup_relative,
                "created_directories": sorted(created_directories), "files": records, **counts}
    backup_root = _validate_manifest(campaign, manifest)  # Includes every long-path/link check before mkdir.
    _safe_path(backup_root, "install-manifest.json")
    _safe_path(backup_root, "uninstalled-native-media-install-manifest.json")
    _safe_path(backup_root, "journal-00000000/transaction.json")
    pending = _safe_path(campaign, PENDING_DIRECTORY)
    journal_path = _safe_path(pending, "transaction.json")
    journal = {"operation": "install", "phase": "preparing", "manifest": manifest}
    pending.mkdir()  # Exclusive reservation also blocks concurrent operations.
    try:
        _write_json(journal_path, journal)
        backup_root.mkdir(parents=True, exist_ok=False)
        for record in records:
            relative = record["relative_path"]
            if record["had_original"]:
                _copy_verified(_safe_path(campaign, relative), _safe_path(backup_root, "original/" + relative),
                               record["original_sha256"], None)
            _copy_verified(sources[relative], _safe_path(backup_root, "payload/" + relative),
                           record["installed_sha256"], None)
        _write_json(_safe_path(backup_root, "install-manifest.json"), manifest)
        journal = {**journal, "phase": "applying"}
        _write_json(journal_path, journal)
        for record in records:
            relative = record["relative_path"]
            _copy_verified(_safe_path(backup_root, "payload/" + relative), _safe_path(campaign, relative),
                           record["installed_sha256"], record["original_sha256"])
        _write_json(manifest_path, manifest)
        _finish_journal(campaign, manifest)
    except Exception:
        if journal_path.is_file():
            _failed_transaction(campaign, journal)
        elif pending.is_dir() and not any(pending.iterdir()):
            pending.rmdir()
        raise
    print(f"Installed {counts['localization_files']} localization files and {len(audio)} audio files in: {campaign}")
    print(f"Canonical XMLs unchanged. Recovery copies retained at: {backup_root}")


def uninstall(campaign: Path) -> None:
    campaign = _campaign(campaign)
    _no_pending(campaign)
    manifest, backup_root = _load_manifest(campaign)
    _validate_backups(campaign, manifest, backup_root)
    for record in manifest["files"]:
        _assert_hash(_safe_path(campaign, record["relative_path"]), record["installed_sha256"])
    archived = _safe_path(backup_root, "uninstalled-native-media-install-manifest.json")
    if archived.exists() and load_json(archived) != manifest:
        raise ValueError("Unexpected archived manifest; refusing to overwrite it")
    pending = _safe_path(campaign, PENDING_DIRECTORY)
    journal_path = _safe_path(pending, "transaction.json")
    journal = {"operation": "uninstall", "phase": "applying", "manifest": manifest}
    pending.mkdir()
    try:
        _write_json(journal_path, journal)
        _write_json(archived, manifest)  # Archive before removing files, including on a fresh installation.
        for record in manifest["files"]:
            relative = record["relative_path"]
            destination = _safe_path(campaign, relative)
            if record["had_original"]:
                _copy_verified(_safe_path(backup_root, "original/" + relative), destination,
                               record["original_sha256"], record["installed_sha256"])
            else:
                _assert_hash(destination, record["installed_sha256"])
                destination.unlink()
        _safe_path(campaign, INSTALL_MANIFEST).unlink()
        _remove_created_directories(campaign, manifest)
        _finish_journal(campaign, manifest)
    except Exception:
        if journal_path.is_file():
            _failed_transaction(campaign, journal)
        elif pending.is_dir() and not any(pending.iterdir()):
            pending.rmdir()
        raise
    print(f"Removed native localization and restored previous files. Recovery copies retained at: {backup_root}")


def verify(campaign: Path) -> None:
    campaign = _campaign(campaign)
    _no_pending(campaign)
    manifest, backup_root = _load_manifest(campaign)
    _, localization, _ = validate_payload(campaign)
    _validate_backups(campaign, manifest, backup_root)
    for record in manifest["files"]:
        relative = record["relative_path"]
        if record["kind"] == "localization" and sha256(localization[relative.removeprefix("localization/")]) != record["installed_sha256"]:
            raise ValueError("Installed XML manifest differs from this release payload")
        _assert_hash(_safe_path(campaign, relative), record["installed_sha256"])
    print(f"Verified {len(manifest['files'])} owned files, all recovery copies and the canonical baseline.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("install", "verify", "uninstall", "recover"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("campaign_directory")
    args = parser.parse_args()
    if sys.version_info < (3, 11):
        parser.error("Python 3.11 or newer is required")
    campaign = Path(args.campaign_directory)
    if args.command == "install":
        install(campaign)
    elif args.command == "verify":
        verify(campaign)
    elif args.command == "uninstall":
        uninstall(campaign)
    else:
        recover(campaign)


if __name__ == "__main__":
    main()
