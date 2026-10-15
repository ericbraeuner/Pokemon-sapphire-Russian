#!/usr/bin/env python3
"""Merge a learner-ROM counter snapshot into an external learner profile."""

from __future__ import annotations

import argparse
import copy
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import context_catalog

LEVEL_INTERNAL = {"A1": 8, "A2": 24, "B1": 40, "B2": 56, "C1": 74, "C2": 92}
LANGUAGES = {"ru", "de"}


def _timestamp(value: Any) -> None:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("captured_at must be a UTC ISO 8601 timestamp ending in Z")
    datetime.fromisoformat(value[:-1] + "+00:00")


def validate_snapshot(snapshot: dict[str, Any]) -> None:
    required = {"schema_version", "source_id", "selected_language", "cefr",
                "exposure_count", "dictionary_count", "last_exposure_context",
                "last_dictionary_context", "session_id", "events", "captured_at"}
    missing = required - snapshot.keys()
    if missing:
        raise ValueError(f"snapshot missing keys: {', '.join(sorted(missing))}")
    if snapshot["schema_version"] != 1 or snapshot["selected_language"] not in LANGUAGES:
        raise ValueError("unsupported snapshot schema or language")
    if snapshot["cefr"] not in LEVEL_INTERNAL:
        raise ValueError("unsupported CEFR level")
    if not isinstance(snapshot["source_id"], str) or not snapshot["source_id"].strip():
        raise ValueError("source_id must be a non-empty string")
    if not isinstance(snapshot["session_id"], str) or not snapshot["session_id"].strip():
        raise ValueError("session_id must be a non-empty string")
    for name in ("exposure_count", "dictionary_count", "last_exposure_context",
                 "last_dictionary_context"):
        if not isinstance(snapshot[name], int) or not 0 <= snapshot[name] <= 0xFFFF:
            raise ValueError(f"{name} must be an unsigned 16-bit integer")
    _timestamp(snapshot["captured_at"])
    previous_sequence = 0
    for event in snapshot["events"]:
        if not isinstance(event, dict) or set(event) != {"sequence", "kind", "context", "delta", "captured_at"}:
            raise ValueError("invalid activity event")
        if not isinstance(event["sequence"], int) or event["sequence"] <= previous_sequence:
            raise ValueError("activity event sequences must be strictly increasing")
        if event["kind"] not in {"exposure", "dictionary"}:
            raise ValueError("invalid activity event kind")
        if not isinstance(event["context"], int) or not 0 <= event["context"] <= 0xFFFF:
            raise ValueError("invalid activity event context")
        if not isinstance(event["delta"], int) or event["delta"] < 1:
            raise ValueError("invalid activity event delta")
        _timestamp(event["captured_at"])
        previous_sequence = event["sequence"]


def merge(profile: dict[str, Any], snapshot: dict[str, Any], *, allow_reset: bool = False) -> dict[str, Any]:
    validate_snapshot(snapshot)
    result = copy.deepcopy(profile)
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
    catalogue = context_catalog.load()
    activity = result.setdefault("activity_vocabulary", {})
    cursors = dict(previous.get("event_cursors", {})) if previous else {}
    cursor = cursors.get(snapshot["session_id"], 0)
    for event in snapshot["events"]:
        if event["sequence"] <= cursor:
            continue
        context = catalogue.get(event["context"])
        if context is None:
            raise ValueError(f"unknown learner activity context: 0x{event['context']:04X}")
        for word in context["words"][snapshot["selected_language"]]:
            state = activity.setdefault(word["id"], {
                "lemma": word["lemma"], "english_gloss": word["english_gloss"],
                "exposure_count": 0, "dictionary_requests": 0, "last_seen": None,
            })
            counter = "exposure_count" if event["kind"] == "exposure" else "dictionary_requests"
            state[counter] += event["delta"]
            state["last_seen"] = event["captured_at"]
        cursor = event["sequence"]
    cursors[snapshot["session_id"]] = cursor
    result["rom_learning"] = {
        "source_id": snapshot["source_id"],
        "exposure_count": exposure_count,
        "dictionary_count": dictionary_count,
        "last_exposure_context": snapshot["last_exposure_context"],
        "last_dictionary_context": snapshot["last_dictionary_context"],
        "event_cursors": cursors,
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
