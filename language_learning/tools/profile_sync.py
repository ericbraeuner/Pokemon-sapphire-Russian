#!/usr/bin/env python3
"""Merge a learner-ROM counter snapshot into an external learner profile."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

LEVEL_INTERNAL = {"A1": 8, "A2": 24, "B1": 40, "B2": 56, "C1": 74, "C2": 92}
LANGUAGES = {"ru", "de"}


def _timestamp(value: Any) -> None:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("captured_at must be a UTC ISO 8601 timestamp ending in Z")
    datetime.fromisoformat(value[:-1] + "+00:00")


def validate_snapshot(snapshot: dict[str, Any]) -> None:
    required = {"schema_version", "source_id", "selected_language", "cefr",
                "exposure_count", "dictionary_count", "captured_at"}
    missing = required - snapshot.keys()
    if missing:
        raise ValueError(f"snapshot missing keys: {', '.join(sorted(missing))}")
    if snapshot["schema_version"] != 1 or snapshot["selected_language"] not in LANGUAGES:
        raise ValueError("unsupported snapshot schema or language")
    if snapshot["cefr"] not in LEVEL_INTERNAL:
        raise ValueError("unsupported CEFR level")
    if not isinstance(snapshot["source_id"], str) or not snapshot["source_id"].strip():
        raise ValueError("source_id must be a non-empty string")
    for name in ("exposure_count", "dictionary_count"):
        if not isinstance(snapshot[name], int) or not 0 <= snapshot[name] <= 0xFFFF:
            raise ValueError(f"{name} must be an unsigned 16-bit integer")
    _timestamp(snapshot["captured_at"])


def merge(profile: dict[str, Any], snapshot: dict[str, Any], *, allow_reset: bool = False) -> dict[str, Any]:
    validate_snapshot(snapshot)
    result = dict(profile)
    previous = profile.get("rom_learning")
    if previous and previous.get("source_id") == snapshot["source_id"] and not allow_reset:
        for name in ("exposure_count", "dictionary_count"):
            if snapshot[name] < previous[name]:
                raise ValueError(f"{name} moved backwards; pass --allow-reset for a new or rewound save")
    exposure_count = snapshot["exposure_count"]
    dictionary_count = snapshot["dictionary_count"]
    result["selected_language"] = snapshot["selected_language"]
    difficulty = dict(result["current_learner_difficulty"])
    if difficulty["cefr"] != snapshot["cefr"]:
        difficulty = {"cefr": snapshot["cefr"], "internal": LEVEL_INTERNAL[snapshot["cefr"]]}
    result["current_learner_difficulty"] = difficulty
    result["rom_learning"] = {
        "source_id": snapshot["source_id"],
        "exposure_count": exposure_count,
        "dictionary_count": dictionary_count,
        "dictionary_rate": round(dictionary_count / exposure_count, 4) if exposure_count else 0.0,
        "last_synced": snapshot["captured_at"],
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", type=Path)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--allow-reset", action="store_true")
    args = parser.parse_args()
    profile = json.loads(args.profile.read_text(encoding="utf-8"))
    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    updated = merge(profile, snapshot, allow_reset=args.allow_reset)
    temporary = args.profile.with_suffix(args.profile.suffix + ".tmp")
    temporary.write_text(json.dumps(updated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(args.profile)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
