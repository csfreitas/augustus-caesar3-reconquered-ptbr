#!/usr/bin/env python3
"""Copy localized overlays to the exact scenario stems used by Reconquered.

The public Settings.xml uses six SAVE.svx names and Valencia rather than the
Valentia spelling used by the message source. Only our localization payload is
copied: the public scenarios, settings, saves and message UIDs remain unchanged.
"""

from __future__ import annotations

import argparse
from pathlib import Path


LOCALIZATION_DIRECTORY = (
    Path(__file__).resolve().parent / "Reconquered Campaign" / "localization" / "pt-BR"
)
SCENARIO_ALIASES = {
    "RC08 Mediolanum": "RC08 Mediolanum SAVE",
    "RC10 Carthago": "RC10 Carthago SAVE",
    "RC11 Tarsus": "RC11 Tarsus SAVE",
    "RC13 Valentia": "RC13 Valencia",
    "RC14 Lutetia": "RC14 Lutetia SAVE",
    "RC17 Londinium": "RC17 Londinium SAVE",
    "RC19 Lindum": "RC19 Lindum SAVE",
}
# Empire overlays follow the actual MAPX names, so RC13 already uses Valencia.
EMPIRE_SCENARIO_ALIASES = {
    source: alias for source, alias in SCENARIO_ALIASES.items()
    if source != "RC13 Valentia"
}


def generate(check: bool, localization_directory: Path = LOCALIZATION_DIRECTORY) -> None:
    pending: list[tuple[Path, bytes]] = []
    kinds = {"messages": SCENARIO_ALIASES, "media": SCENARIO_ALIASES}
    # Packages without imperial localization can still use message/media aliases.
    if (localization_directory / "empire").is_dir():
        kinds["empire"] = EMPIRE_SCENARIO_ALIASES
    for kind, scenario_aliases in kinds.items():
        directory = localization_directory / kind
        for source_name, alias_name in scenario_aliases.items():
            source = directory / f"{source_name}.xml"
            if not source.is_file():
                raise FileNotFoundError(f"Missing canonical localized overlay: {source}")
            content = source.read_bytes()
            destination = directory / f"{alias_name}.xml"
            if not destination.is_file() or destination.read_bytes() != content:
                pending.append((destination, content))

    # Validate every source before writing any alias, and never write in check mode.
    if check and pending:
        raise ValueError(f"Scenario aliases are missing or out of date: {[str(p) for p, _ in pending]}")
    for destination, content in pending:
        destination.write_bytes(content)
    action = "Validated" if check else "Generated"
    total = sum(len(scenario_aliases) for scenario_aliases in kinds.values())
    print(f"{action} {total} scenario aliases ({', '.join(kinds)}).")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="check aliases without changing files")
    args = parser.parse_args()
    generate(args.check)


if __name__ == "__main__":
    main()
