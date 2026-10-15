#!/usr/bin/env python3
"""Build wrapper-ready adaptive dialogue selections for an unlocked profile."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import adaptive_selector


ROOT = Path(__file__).resolve().parents[1]


def _timestamp(value: str | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    parsed = adaptive_selector._time(value)
    if parsed is None:
        raise ValueError("generated-at timestamp is required")
    return parsed


def build(pack: dict[str, Any], profile: dict[str, Any], catalogue: dict[str, Any],
          *, now: datetime | None = None) -> dict[str, Any]:
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    available = {item["dialogue_id"] for item in pack["dialogues"]}
    selections = []
    eligible = 0
    for entry in catalogue["dialogues"]:
        dialogue_id = entry["id"]
        if dialogue_id not in available:
            continue
        dialogue = next(item for item in pack["dialogues"]
                        if item["dialogue_id"] == dialogue_id)
        if not any(adaptive_selector._progress_allows(profile, variant)
                   for variant in dialogue["variants"]):
            continue
        eligible += 1
        try:
            selection = adaptive_selector.select(
                pack, profile, dialogue_id, now=now,
            )
        except ValueError as error:
            if str(error) != "no dialogue variant is compatible with learner difficulty and progress":
                raise
            continue
        selection["source_symbol"] = entry["source"]["base_text_symbol"]
        selections.append(selection)
    generated_at = now.isoformat().replace("+00:00", "Z")
    return {
        "schema_version": 1,
        "profile_id": profile["profile_id"],
        "selected_language": pack["target_language"]["tag"],
        "cefr": profile["current_learner_difficulty"]["cefr"],
        "generated_at": generated_at,
        "game_progress": profile["game_progress"],
        "eligible_dialogue_count": eligible,
        "selection_count": len(selections),
        "selections": selections,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--generated-at", help="fixed UTC timestamp for reproducible output")
    args = parser.parse_args()
    profile = json.loads(args.profile.read_text(encoding="utf-8"))
    tag = profile["selected_language"]
    pack = json.loads((ROOT / "language_packs" / tag / "pack.json").read_text(encoding="utf-8"))
    catalogue = json.loads((ROOT / "integration/dialogue_catalog.json").read_text(encoding="utf-8"))
    plan = build(pack, profile, catalogue, now=_timestamp(args.generated_at))
    args.output.write_text(
        json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
