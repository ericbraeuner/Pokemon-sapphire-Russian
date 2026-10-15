#!/usr/bin/env python3
"""Select a language-pack dialogue variant for an external learner profile."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _time(value: str | None) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("review timestamps must be UTC ISO 8601 strings ending in Z")
    return datetime.fromisoformat(value[:-1] + "+00:00")


def _progress_allows(profile: dict[str, Any], variant: dict[str, Any]) -> bool:
    required = variant.get("minimum_game_progress")
    if not required:
        return True
    progress = profile["game_progress"]
    return (progress["chapter"] == required.get("chapter", progress["chapter"])
            and progress["sequence"] >= required.get("sequence", 0))


def select(pack: dict[str, Any], profile: dict[str, Any], dialogue_id: str,
           *, now: datetime | None = None) -> dict[str, Any]:
    language = pack["target_language"]["tag"]
    if profile["selected_language"] != language:
        raise ValueError("profile language does not match language pack")
    dialogue = next((item for item in pack["dialogues"]
                     if item["dialogue_id"] == dialogue_id), None)
    if dialogue is None:
        raise ValueError(f"dialogue not found in language pack: {dialogue_id}")
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    states = profile.get("vocabulary", {})
    difficulty = profile["current_learner_difficulty"]["internal"]
    candidates = []
    for variant in dialogue["variants"]:
        if variant["internal_difficulty"] > difficulty or not _progress_allows(profile, variant):
            continue
        word_states = [states.get(word_id) for word_id in variant["vocabulary_ids"]]
        unseen = sum(state is None or state.get("exposure_count", 0) == 0 for state in word_states)
        if unseen > variant.get("new_vocabulary_budget", unseen):
            continue
        due = sum(
            state is not None and _time(state.get("next_review")) is not None
            and _time(state.get("next_review")) <= now
            for state in word_states
        )
        known = [state.get("mastery", 0.0) for state in word_states if state is not None]
        mastery = round(sum(known) / len(known), 4) if known else 0.0
        candidates.append((variant["internal_difficulty"], due, mastery, variant))
    if not candidates:
        raise ValueError("no dialogue variant is compatible with learner difficulty and progress")
    difficulty_score, due_count, mastery, variant = max(
        candidates, key=lambda item: (item[0], item[1], item[2], item[3]["id"])
    )
    return {
        "schema_version": 1,
        "dialogue_id": dialogue_id,
        "variant_id": variant["id"],
        "selected_language": language,
        "cefr": variant["cefr"],
        "internal_difficulty": difficulty_score,
        "due_vocabulary_count": due_count,
        "average_known_mastery": mastery,
        "text": variant["text"],
        "english_gloss": variant["english_gloss"],
        "vocabulary_ids": variant["vocabulary_ids"],
        "grammar_note_ids": variant["grammar_note_ids"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pack", type=Path)
    parser.add_argument("profile", type=Path)
    parser.add_argument("dialogue_id")
    parser.add_argument("--now", help="fixed UTC timestamp for reproducible selection")
    args = parser.parse_args()
    pack = json.loads(args.pack.read_text(encoding="utf-8"))
    profile = json.loads(args.profile.read_text(encoding="utf-8"))
    now = _time(args.now) if args.now else None
    rendered = json.dumps(select(pack, profile, args.dialogue_id, now=now),
                          ensure_ascii=False, indent=2) + "\n"
    sys.stdout.buffer.write(rendered.encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
