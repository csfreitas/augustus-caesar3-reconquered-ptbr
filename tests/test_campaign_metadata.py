from pathlib import Path
import json
import unittest
import xml.etree.ElementTree as ET

import generate_scenario_aliases as aliases
import reconquered_ptbr_native_media as native

ROOT = Path(__file__).resolve().parents[1]
METADATA = ROOT / "Reconquered Campaign/localization/pt-BR/campaign.xml"
# Exact identities from the supported public campaign, not display names.
SCENARIOS = (
    "RC01 Ostia", "RC02 Brundisium", "RC03 Capua", "RC04 Tarentum",
    "RC05 Tarraco", "RC06 Syracusae", "RC07 Miletus", "RC08 Mediolanum SAVE",
    "RC09 Lugdunum", "RC10 Carthago SAVE", "RC11 Tarsus SAVE", "RC12 Tingis",
    "RC13 Valencia", "RC14 Lutetia SAVE", "RC15 Caesarea", "RC16 Damascus",
    "RC17 Londinium SAVE", "RC18 Sarmizegetusa", "RC19 Lindum SAVE", "RC20 Massilia",
)


# Object IDs and source names decoded from the supported v18 MAPX baseline.
# The six SAVE.svx files have matching (object ID, source name) pairs.
EMPIRE_OBJECTS = {
    "RC01 Ostia": [(13, "Ostia"), (14, "Rome"), (17, "Croton"), (32, "Veii"), (33, "Syracusae")],
    "RC02 Brundisium": [(61, "Rome"), (77, "Syracusae"), (78, "Croton")],
    "RC03 Capua": [(60, "Rome"), (77, "Syracusae"), (78, "Croton")],
    "RC04 Tarentum": [(73, "Rome"), (88, "Croton")],
    "RC05 Tarraco": [(115, "Rome"), (130, "Syracusae")],
    "RC06 Syracusae": [(108, "Syracusae"), (130, "Rome"), (157, "Croton")],
    "RC07 Miletus": [(145, "Miletus"), (172, "Rome"), (176, "Syracusae")],
    "RC08 Mediolanum": [(118, "Rome"), (126, "Syracusae")],
    "RC09 Lugdunum": [(325, "Rome"), (330, "Miletus"), (333, "Syracusae")],
    "RC10 Carthago": [(286, "Syracusae"), (337, "Rome")],
    "RC11 Tarsus": [(254, "Tarsus"), (255, "Miletus"), (335, "Rome"), (342, "Syracusae")],
    "RC12 Tingis": [(303, "Rome")],
    "RC13 Valencia": [(152, "Valencia"), (166, "Rome"), (261, "Ruins of Carthago")],
    "RC14 Lutetia": [(280, "Rome"), (327, "Valencia")],
    "RC15 Caesarea": [(293, "Rome"), (295, "Valencia")],
    "RC16 Damascus": [(254, "Damascus"), (255, "Miletus"), (286, "Tarsus"), (326, "Far East"), (330, "Rome"), (337, "Syracusae")],
    "RC17 Londinium": [(107, "Rome"), (115, "Syracusae")],
    "RC18 Sarmizegetusa": [(100, "Rome"), (102, "Valencia")],
    "RC19 Lindum": [(86, "Hadrians Wall"), (116, "Rome"), (124, "Syracusae")],
    "RC20 Massilia": [(126, "Rome")],
}
EMPIRE_NAMES = {
    "Rome": "Roma",
    "Ostia": "Óstia",
    "Croton": "Crotona",
    "Veii": "Veios",
    "Syracusae": "Siracusa",
    "Miletus": "Mileto",
    "Tarsus": "Tarso",
    "Valencia": "Valentia",
    "Damascus": "Damasco",
    "Ruins of Carthago": "Ruínas de Cartago",
    "Far East": "Extremo Oriente",
    "Hadrians Wall": "Muralha de Adriano",
}


class CampaignMetadataTest(unittest.TestCase):
    def test_packaged_paths_cover_every_canonical_scenario(self):
        plan = json.loads((ROOT / "MEDIA_INTEGRATION_PLAN.json").read_text(encoding="utf-8"))
        expected = native.expected_localization_paths(plan)
        localization = METADATA.parent.parent
        actual = {path.relative_to(localization).as_posix()
                  for path in localization.rglob("*") if path.is_file()}
        self.assertEqual(actual, expected)
        self.assertEqual(len(expected), 82)
        for scenario in SCENARIOS:
            for kind in ("messages", "media", "empire"):
                self.assertIn(f"pt-BR/{kind}/{scenario}.xml", expected)

    def test_imperial_city_name_overlays_are_source_guarded(self):
        expected = dict(EMPIRE_OBJECTS)
        for source, alias in aliases.EMPIRE_SCENARIO_ALIASES.items():
            expected[alias] = expected[source]
        self.assertEqual(len(expected), 26)
        self.assertEqual(sum(len(entries) for entries in EMPIRE_OBJECTS.values()), 54)
        self.assertEqual(set(expected), native.EMPIRE_LOCALIZATION_SCENARIOS)
        for scenario, entries in expected.items():
            with self.subTest(scenario=scenario):
                path = METADATA.parent / "empire" / f"{scenario}.xml"
                root = ET.parse(path).getroot()
                self.assertEqual(root.tag, "empire_localization")
                self.assertEqual(root.attrib, {"version": "1"})
                cities = list(root)
                self.assertEqual(len(cities), len(entries))
                self.assertEqual(len({city.get("object-id") for city in cities}), len(entries))
                for city, (object_id, source) in zip(cities, entries):
                    self.assertEqual(city.tag, "city")
                    self.assertEqual(city.attrib, {"object-id": str(object_id), "source": source})
                    self.assertEqual([field.tag for field in city], ["name"])
                    self.assertEqual(city.findtext("name"), EMPIRE_NAMES[source])
                    city.findtext("name").encode("cp1252", errors="strict")
        for source, alias in aliases.EMPIRE_SCENARIO_ALIASES.items():
            self.assertEqual((METADATA.parent / "empire" / f"{source}.xml").read_bytes(),
                             (METADATA.parent / "empire" / f"{alias}.xml").read_bytes())

    def test_all_campaign_mission_and_scenario_fields_are_present(self):
        root = ET.parse(METADATA).getroot()
        self.assertEqual(root.tag, "campaign_localization")
        self.assertEqual(root.attrib, {"version": "1", "language": "pt-BR"})
        missions = root.findall("mission")
        scenarios = root.findall("scenario")
        self.assertEqual([m.get("first-scenario") for m in missions], list(SCENARIOS))
        self.assertEqual([s.get("file") for s in scenarios], list(SCENARIOS))
        self.assertEqual(len(list(root)), 42)
        for mission in missions:
            self.assertEqual(mission.attrib, {"first-scenario": mission.get("first-scenario")})
            self.assertEqual([field.tag for field in mission], ["title"])
        for scenario in scenarios:
            self.assertEqual(scenario.attrib, {"file": scenario.get("file")})
            self.assertEqual([field.tag for field in scenario], ["name", "description"])
        fields = [root.find("name"), root.find("description")]
        fields += [m.find("title") for m in missions]
        fields += [field for s in scenarios for field in s]
        self.assertEqual(len(fields), 62)
        for field in fields:
            self.assertIsNotNone(field)
            self.assertTrue(field.text and field.text.strip())
            self.assertNotIn("[QA]", field.text)
            self.assertNotIn("TESTE", field.text)
            self.assertNotIn("Teste de exibição", field.text)
            # Portuguese assets use the game's Western encoding.
            field.text.encode("cp1252", errors="strict")


if __name__ == "__main__":
    unittest.main()
