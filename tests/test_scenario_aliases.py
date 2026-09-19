from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import generate_scenario_aliases as aliases


class ScenarioAliasesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.localization = self.root / "localization" / "pt-BR"
        self.sources: dict[Path, bytes] = {}
        for kind in ("messages", "media"):
            directory = self.localization / kind
            directory.mkdir(parents=True)
            for name in aliases.SCENARIO_ALIASES:
                path = directory / f"{name}.xml"
                # Preserve Unicode, line endings and source bytes rather than reserializing.
                content = ('\ufeff<test name="' + name + '">ação, Óstia</test>\r\n').encode("utf-8")
                path.write_bytes(content)
                self.sources[path] = content

    def alias_paths(self) -> list[Path]:
        return [
            self.localization / kind / f"{name}.xml"
            for kind in ("messages", "media")
            for name in aliases.SCENARIO_ALIASES.values()
        ]

    def add_empire_sources(self) -> dict[Path, bytes]:
        directory = self.localization / "empire"
        directory.mkdir()
        sources = {}
        for source in aliases.EMPIRE_SCENARIO_ALIASES:
            path = directory / f"{source}.xml"
            content = ('\ufeff<test name="' + source + '">Roma, Óstia</test>\r\n').encode("utf-8")
            path.write_bytes(content)
            sources[path] = content
        return sources

    def empire_alias_paths(self) -> list[Path]:
        return [self.localization / "empire" / f"{name}.xml"
                for name in aliases.EMPIRE_SCENARIO_ALIASES.values()]

    def test_exact_seven_public_scenario_aliases(self) -> None:
        self.assertEqual(set(aliases.SCENARIO_ALIASES.values()), {
            "RC08 Mediolanum SAVE", "RC10 Carthago SAVE", "RC11 Tarsus SAVE",
            "RC13 Valencia", "RC14 Lutetia SAVE", "RC17 Londinium SAVE", "RC19 Lindum SAVE",
        })

    def test_empire_aliases_use_save_names_and_valencia_is_already_canonical(self) -> None:
        self.assertEqual(set(aliases.EMPIRE_SCENARIO_ALIASES.values()), {
            "RC08 Mediolanum SAVE", "RC10 Carthago SAVE", "RC11 Tarsus SAVE",
            "RC14 Lutetia SAVE", "RC17 Londinium SAVE", "RC19 Lindum SAVE",
        })
        self.assertNotIn("RC13 Valentia", aliases.EMPIRE_SCENARIO_ALIASES)

    def test_optional_empire_aliases_preserve_bytes_and_valencia(self) -> None:
        sources = self.add_empire_sources()
        valencia = self.localization / "empire" / "RC13 Valencia.xml"
        valencia_content = b"already matches the canonical scenario name"
        valencia.write_bytes(valencia_content)
        aliases.generate(False, self.localization)
        aliases.generate(True, self.localization)
        for source, alias in aliases.EMPIRE_SCENARIO_ALIASES.items():
            directory = self.localization / "empire"
            self.assertEqual((directory / f"{source}.xml").read_bytes(),
                             (directory / f"{alias}.xml").read_bytes())
        for path, content in sources.items():
            self.assertEqual(path.read_bytes(), content)
        self.assertEqual(valencia.read_bytes(), valencia_content)
        self.assertFalse(valencia.with_name("RC13 Valentia.xml").exists())

    def test_missing_empire_source_prevents_all_alias_writes(self) -> None:
        sources = self.add_empire_sources()
        list(sources)[-1].unlink()
        with self.assertRaisesRegex(FileNotFoundError, "Missing canonical localized overlay"):
            aliases.generate(False, self.localization)
        self.assertTrue(all(not path.exists()
                            for path in self.alias_paths() + self.empire_alias_paths()))

    def test_check_missing_or_stale_empire_alias_does_not_write(self) -> None:
        self.add_empire_sources()
        aliases.generate(False, self.localization)
        missing, stale = self.empire_alias_paths()[:2]
        missing.unlink()
        stale.write_bytes(b"outdated empire")
        with self.assertRaisesRegex(ValueError, "missing or out of date"):
            aliases.generate(True, self.localization)
        self.assertFalse(missing.exists())
        self.assertEqual(stale.read_bytes(), b"outdated empire")

    def test_generate_preserves_source_bytes_and_other_campaign_files(self) -> None:
        untouched = {
            self.root / "Settings.xml": b"canonical settings",
            self.root / "Ostia-Teste.svx": b"saved game",
            self.localization / "campaign.xml": b"localized metadata",
        }
        for path, content in untouched.items():
            path.write_bytes(content)
        aliases.generate(False, self.localization)
        for kind in ("messages", "media"):
            for source, alias in aliases.SCENARIO_ALIASES.items():
                directory = self.localization / kind
                self.assertEqual((directory / f"{source}.xml").read_bytes(),
                                 (directory / f"{alias}.xml").read_bytes())
        for path, content in self.sources.items() | untouched.items():
            self.assertEqual(path.read_bytes(), content)
        self.assertEqual(len(self.alias_paths()), 14)

    def test_check_missing_aliases_does_not_write(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing or out of date"):
            aliases.generate(True, self.localization)
        self.assertTrue(all(not path.exists() for path in self.alias_paths()))

    def test_check_stale_alias_does_not_overwrite(self) -> None:
        aliases.generate(False, self.localization)
        stale = self.alias_paths()[0]
        stale.write_bytes(b"outdated")
        with self.assertRaisesRegex(ValueError, "missing or out of date"):
            aliases.generate(True, self.localization)
        self.assertEqual(stale.read_bytes(), b"outdated")

    def test_check_and_regeneration_are_idempotent(self) -> None:
        aliases.generate(False, self.localization)
        times = {path: path.stat().st_mtime_ns for path in self.alias_paths()}
        aliases.generate(True, self.localization)
        aliases.generate(False, self.localization)
        self.assertEqual(times, {path: path.stat().st_mtime_ns for path in self.alias_paths()})

    def test_missing_source_prevents_partial_writes(self) -> None:
        missing = list(self.sources)[-1]
        missing.unlink()
        with self.assertRaisesRegex(FileNotFoundError, "Missing canonical localized overlay"):
            aliases.generate(False, self.localization)
        self.assertTrue(all(not path.exists() for path in self.alias_paths()))


if __name__ == "__main__":
    unittest.main()
