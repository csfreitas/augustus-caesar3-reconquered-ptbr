"""Regressions for visible English and rich-text commands in the PT-BR payload."""

import re
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

MESSAGES = Path(__file__).resolve().parents[1] / "Reconquered Campaign/localization/pt-BR/messages"
# The numeric prefix starts a highlighted word. H/L/P are standalone commands;
# allowing them before a word would mistake e.g. @Honorum for a heading.
COMMAND = re.compile(r"@(?:G\[[^\]\r\n]+\]|G\d+|[HLP](?=\s|@|$)|\d+)")
ENGLISH_HIGHLIGHTS = {
    "assignment", "blockade", "bricks", "buildup", "clay", "climate",
    "corruption", "deposits", "forts", "furniture", "gold", "iron",
    "magnate", "marble", "mining", "olives", "option", "ore", "poverty",
    "province", "provinces", "sand", "saturation", "self-sufficiency",
    "shortages", "stone", "tensions", "timber", "undesirable", "unpleasant",
    "weapons", "wilderness", "workshops",
}


class MessageTextTest(unittest.TestCase):
    def fields(self):
        for path in sorted(MESSAGES.glob("*.xml")):
            root = ET.parse(path).getroot()
            for message in root.findall("message"):
                for field in ("title", "subtitle", "text"):
                    yield path.name, message.get("uid"), field, message.findtext(field, "")

    def test_rich_text_commands_do_not_consume_highlighted_words(self):
        errors = []
        for name, uid, field, text in self.fields():
            for match in re.finditer("@", text):
                if not COMMAND.match(text, match.start()):
                    errors.append((name, uid, field, text[match.start():match.start() + 35]))
        self.assertEqual(errors, [], "Use @0 before highlighted words, preserving real H/L/P/G commands")

    def test_known_english_highlights_are_translated(self):
        errors = []
        for name, uid, field, text in self.fields():
            # Asset filenames, UIDs and Latin terms are not translation omissions.
            words = re.findall(r"@(?:0)?([A-Za-z]+(?:-[A-Za-z]+)*)", text)
            for word in words:
                if word.casefold() in ENGLISH_HIGHLIGHTS:
                    errors.append((name, uid, field, word))
        self.assertEqual(errors, [])

    def test_instruction_icon_uses_existing_baseline_filename(self):
        for path in sorted(MESSAGES.glob("*.xml")):
            with self.subTest(file=path.name):
                text = ET.parse(path).getroot().findtext("message[@uid='intro']/text", "")
                self.assertTrue("@G[c3_instructions_icon.png]" in text, "Missing instruction icon")
                self.assertFalse("@G[c3 instructions icon.png]" in text, "Broken legacy icon reference")

    def test_highlighted_quantities_are_not_parsed_as_link_ids(self):
        for name, uid, field, text in self.fields():
            with self.subTest(file=name, uid=uid, field=field):
                self.assertIsNone(re.search(r"@0\d", text), "Separate @0 from a highlighted number with a space")

    def test_approved_city_and_building_terms(self):
        outdated = re.compile(r"Valência|Lutécia|Massília|Pérgamo|Cesareia|Útica|Grande Templo|[Cc]ovas? de leões")
        for name, uid, field, text in self.fields():
            with self.subTest(file=name, uid=uid, field=field):
                self.assertIsNone(outdated.search(text))
        campaign = ET.parse(MESSAGES.parent / "campaign.xml").getroot()
        for field in campaign.iter():
            self.assertIsNone(outdated.search(field.text or ""))

    def test_large_temples_unlock_sanctuaries_not_more_large_temples(self):
        root = ET.parse(MESSAGES / "RC20 Massilia.xml").getroot()
        objective = root.findtext("message[@uid='large temples']/text", "")
        reward = root.findtext("message[@uid='large temples done']/text", "")
        self.assertIn("5 templos grandes e 2 ninfeus", objective)
        self.assertIn("liberar @0santuários", objective)
        self.assertIn("Santuários agora podem ser construídos", reward)


if __name__ == "__main__":
    unittest.main()
