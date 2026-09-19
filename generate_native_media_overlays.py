#!/usr/bin/env python3
"""Generate Augustus native localized-media companions from the approved plans."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from xml.etree import ElementTree

from generate_scenario_aliases import SCENARIO_ALIASES


ROOT = Path(__file__).resolve().parent
MUSIC_PLAN_PATH = ROOT / "MEDIA_INTEGRATION_PLAN.json"
SPEECH_PLAN_PATH = ROOT / "SPEECH_INTEGRATION_PLAN.json"
MESSAGES_DIRECTORY = ROOT / "Reconquered Campaign" / "localization" / "pt-BR" / "messages"
MEDIA_DIRECTORY = ROOT / "Reconquered Campaign" / "localization" / "pt-BR" / "media"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def scenario_name(xml_name: str) -> str:
    suffix = " corrected.xml"
    if not xml_name.endswith(suffix):
        raise ValueError(f"Unexpected canonical XML name: {xml_name}")
    return xml_name.removesuffix(suffix)


def is_simple_filename(filename: str) -> bool:
    return bool(filename) and filename not in {".", ".."} and not any(
        separator in filename for separator in ("/", "\\", ":")
    )


def localized_uids(path: Path) -> set[str]:
    root = ElementTree.parse(path).getroot()
    if root.tag != "localization" or root.attrib.get("version") != "1":
        raise ValueError(f"Invalid localization overlay root: {path}")
    uids = [message.attrib.get("uid") for message in root.findall("message")]
    if any(not uid for uid in uids) or len(uids) != len(set(uids)):
        raise ValueError(f"Missing or duplicate UID in localization overlay: {path}")
    return set(uids)


def resolve_uid_case_insensitive(uids: set[str], requested: str, overlay: Path) -> str:
    matches = [uid for uid in uids if uid.casefold() == requested.casefold()]
    if len(matches) != 1:
        raise ValueError(
            f"Expected exactly one UID matching {requested!r} in {overlay.name}; found {matches}"
        )
    return matches[0]


def build_companion(mission: dict, speech_mission: dict) -> bytes:
    name = scenario_name(mission["xml"])
    overlay = MESSAGES_DIRECTORY / f"{name}.xml"
    if not overlay.is_file():
        raise FileNotFoundError(f"Missing text overlay: {overlay}")
    valid_uids = localized_uids(overlay)

    media_by_uid: dict[str, dict[str, str]] = {}
    for speech in speech_mission["speech"]:
        uid = speech["uid"]
        filename = speech["file"]
        if uid not in valid_uids:
            raise ValueError(f"Speech UID {uid!r} is absent from {overlay.name}")
        if not is_simple_filename(filename):
            raise ValueError(f"Unsafe speech filename: {filename!r}")
        if uid in media_by_uid:
            raise ValueError(f"Duplicate speech UID in {mission['id']}: {uid!r}")
        media_by_uid[uid] = {"speech": filename}

    for requested_uid, filename in (("intro", mission["briefing"]), ("victory", mission["victory"])):
        uid = resolve_uid_case_insensitive(valid_uids, requested_uid, overlay)
        if not is_simple_filename(filename):
            raise ValueError(f"Unsafe music filename: {filename!r}")
        media_by_uid.setdefault(uid, {})["background_music"] = filename

    root = ElementTree.Element("media_localization", {"version": "1", "language": "pt-BR"})
    for uid, media in media_by_uid.items():
        message = ElementTree.SubElement(root, "message", {"uid": uid})
        if "speech" in media:
            ElementTree.SubElement(message, "speech", {"filename": media["speech"]})
        if "background_music" in media:
            ElementTree.SubElement(
                message,
                "background_music",
                {"filename": media["background_music"]},
            )
    ElementTree.indent(root, space="    ")
    return ElementTree.tostring(root, encoding="utf-8", xml_declaration=True) + b"\n"


def generate(check: bool) -> None:
    music_plan = load_json(MUSIC_PLAN_PATH)
    speech_plan = load_json(SPEECH_PLAN_PATH)
    music_by_id = {mission["id"]: mission for mission in music_plan["missions"]}
    speech_by_id = {mission["id"]: mission for mission in speech_plan["missions"]}
    if set(music_by_id) != set(speech_by_id):
        raise ValueError("Music and speech plans cover different missions")

    expected_paths: set[Path] = set()
    changed: list[Path] = []
    for mission_id in sorted(music_by_id):
        mission = music_by_id[mission_id]
        speech_mission = speech_by_id[mission_id]
        if (
            mission["xml"] != speech_mission["xml"]
            or mission["sha256"] != speech_mission["baseline_sha256"]
        ):
            raise ValueError(f"Media plans disagree for {mission_id}")
        destination = MEDIA_DIRECTORY / f"{scenario_name(mission['xml'])}.xml"
        expected_paths.add(destination)
        content = build_companion(mission, speech_mission)
        if not destination.is_file() or destination.read_bytes() != content:
            changed.append(destination)
            if not check:
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(content)

    existing = set(MEDIA_DIRECTORY.glob("*.xml")) if MEDIA_DIRECTORY.is_dir() else set()
    # Aliases are byte-for-byte copies checked by generate_scenario_aliases.py.
    alias_paths = {
        MEDIA_DIRECTORY / f"{alias}.xml"
        for source, alias in SCENARIO_ALIASES.items()
        if MEDIA_DIRECTORY / f"{source}.xml" in expected_paths
    }
    unexpected = sorted(existing - expected_paths - alias_paths)
    if unexpected:
        raise ValueError(f"Unexpected native media companions: {unexpected}")
    if check and changed:
        raise ValueError(f"Native media companions are out of date: {changed}")
    action = "Validated" if check else "Generated"
    print(f"{action} {len(expected_paths)} native localized-media companions.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate that generated companions already match the approved plans",
    )
    args = parser.parse_args()
    generate(args.check)


if __name__ == "__main__":
    main()
