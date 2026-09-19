from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import reconquered_ptbr_native_media as native


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


class NativeMediaInstallerTest(unittest.TestCase):
    def test_install_and_uninstall_without_modifying_canonical_xml(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            campaign = root / "game" / "campaigns" / "Reconquered Campaign"
            payload = root / "payload" / "Reconquered Campaign"
            xml_name = "RC01 Test corrected.xml"
            scenario_name = "RC01 Test"
            xml_content = b"<messages><message uid='intro'/><message uid='victory'/></messages>"
            xml_path = campaign / "xmls" / xml_name
            xml_path.parent.mkdir(parents=True)
            xml_path.write_bytes(xml_content)

            localization = payload / "localization"
            (localization / "pt-BR" / "messages").mkdir(parents=True)
            (localization / "pt-BR" / "media").mkdir(parents=True)
            (localization / "pt-BR" / "empire").mkdir(parents=True)
            (localization / "locales.xml").write_text("<locales version='1'/>", encoding="utf-8")
            (localization / "pt-BR" / "messages" / f"{scenario_name}.xml").write_text(
                "<localization version='1'/>", encoding="utf-8"
            )
            (localization / "pt-BR" / "media" / f"{scenario_name}.xml").write_text(
                "<media_localization version='1'/>", encoding="utf-8"
            )
            for empire_scenario in native.EMPIRE_LOCALIZATION_SCENARIOS:
                (localization / "pt-BR" / "empire" / f"{empire_scenario}.xml").write_text(
                    "<empire_localization version='1'/>", encoding="utf-8"
                )
            metadata_path = localization / "pt-BR" / "campaign.xml"
            metadata_content = b"<campaign_localization version='1'><name>Test</name></campaign_localization>"
            metadata_path.write_bytes(metadata_content)

            audio = payload / "audio"
            audio.mkdir(parents=True)
            audio_content = {
                "briefing.wav": b"briefing",
                "victory.wav": b"victory",
                "briefing-music.wav": b"briefing-music",
                "victory-music.wav": b"victory-music",
            }
            for filename, content in audio_content.items():
                (audio / filename).write_bytes(content)

            music_plan = {
                "version": "1",
                "assets": [
                    {"file": name, "sha256": digest(audio_content[name])}
                    for name in ("briefing-music.wav", "victory-music.wav")
                ],
                "missions": [
                    {
                        "id": "RC01",
                        "xml": xml_name,
                        "sha256": digest(xml_content),
                        "briefing": "briefing-music.wav",
                        "victory": "victory-music.wav",
                    }
                ],
            }
            speech_plan = {
                "version": "1",
                "missions": [
                    {
                        "id": "RC01",
                        "xml": xml_name,
                        "baseline_sha256": digest(xml_content),
                        "speech": [
                            {
                                "uid": "intro",
                                "file": "briefing.wav",
                                "sha256": digest(audio_content["briefing.wav"]),
                            },
                            {
                                "uid": "victory",
                                "file": "victory.wav",
                                "sha256": digest(audio_content["victory.wav"]),
                            },
                        ],
                    }
                ],
            }
            music_plan_path = root / "music.json"
            speech_plan_path = root / "speech.json"
            music_plan_path.write_text(json.dumps(music_plan), encoding="utf-8")
            speech_plan_path.write_text(json.dumps(speech_plan), encoding="utf-8")

            existing_locales = campaign / "localization" / "locales.xml"
            existing_locales.parent.mkdir(parents=True)
            existing_locales.write_bytes(b"previous-locales")
            existing_metadata = campaign / "localization" / "pt-BR" / "campaign.xml"
            existing_metadata.parent.mkdir(parents=True)
            existing_metadata.write_bytes(b"previous-metadata")
            settings = campaign / "Settings.xml"
            settings.write_bytes(b"canonical-settings")
            save = campaign / "example.svx"
            save.write_bytes(b"canonical-save")

            with (
                patch.object(native, "MUSIC_PLAN_PATH", music_plan_path),
                patch.object(native, "SPEECH_PLAN_PATH", speech_plan_path),
                patch.object(native, "PAYLOAD_AUDIO", audio),
                patch.object(native, "PAYLOAD_LOCALIZATION", localization),
            ):
                empire_path = localization / "pt-BR" / "empire" / "RC19 Lindum SAVE.xml"
                empire_content = empire_path.read_bytes()
                empire_path.unlink()
                with self.assertRaisesRegex(ValueError, "RC19 Lindum SAVE.xml"):
                    native.install(campaign)
                self.assertFalse((campaign / native.INSTALL_MANIFEST).exists())
                self.assertFalse((campaign / ".reconquered-ptbr-native-media-backup").exists())
                self.assertEqual(existing_metadata.read_bytes(), b"previous-metadata")
                self.assertEqual(existing_locales.read_bytes(), b"previous-locales")
                empire_path.write_bytes(empire_content)
                metadata_path.unlink()
                with self.assertRaisesRegex(ValueError, "pt-BR/campaign.xml"):
                    native.install(campaign)
                self.assertEqual(existing_metadata.read_bytes(), b"previous-metadata")
                self.assertEqual(existing_locales.read_bytes(), b"previous-locales")
                self.assertFalse((campaign / native.INSTALL_MANIFEST).exists())
                self.assertFalse((campaign / ".reconquered-ptbr-native-media-backup").exists())
                metadata_path.write_bytes(metadata_content)
                native.install(campaign)
                self.assertEqual(xml_path.read_bytes(), xml_content)
                manifest = json.loads((campaign / native.INSTALL_MANIFEST).read_text(encoding="utf-8"))
                self.assertEqual(manifest["localization_files"],
                                 4 + len(native.EMPIRE_LOCALIZATION_SCENARIOS))
                self.assertEqual(manifest["speech_files"], 2)
                self.assertEqual(manifest["music_files"], 2)
                self.assertEqual(len(manifest["files"]),
                                 8 + len(native.EMPIRE_LOCALIZATION_SCENARIOS))
                self.assertEqual(existing_metadata.read_bytes(), metadata_content)
                self.assertEqual(settings.read_bytes(), b"canonical-settings")
                self.assertEqual(save.read_bytes(), b"canonical-save")
                self.assertTrue(
                    (campaign / "localization" / "pt-BR" / "audio" / "briefing.wav").is_file()
                )
                native.verify(campaign)

                native.uninstall(campaign)
                self.assertEqual(xml_path.read_bytes(), xml_content)
                self.assertEqual(existing_locales.read_bytes(), b"previous-locales")
                self.assertEqual(existing_metadata.read_bytes(), b"previous-metadata")
                self.assertEqual(settings.read_bytes(), b"canonical-settings")
                self.assertEqual(save.read_bytes(), b"canonical-save")
                self.assertFalse((campaign / "localization" / "pt-BR" / "media").exists())
                self.assertFalse((campaign / "localization" / "pt-BR" / "empire").exists())
                self.assertFalse((campaign / "localization" / "pt-BR" / "audio").exists())


if __name__ == "__main__":
    unittest.main()
