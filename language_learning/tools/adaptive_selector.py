#!/usr/bin/env python3
"""Select a language-pack dialogue variant for an external learner profile."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _combined_states(pack: dict[str, Any], profile: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Resolve context activity back to stable pack vocabulary IDs by lemma."""
    states = {key: dict(value) for key, value in profile.get("vocabulary", {}).items()}
    for state in states.values():
        state.setdefault("dictionary_requests", state.get("hint_requests", 0))
    activity_by_lemma: dict[str, list[dict[str, Any]]] = {}
    for state in profile.get("activity_vocabulary", {}).values():
        lemma = state.get("lemma")
        if isinstance(lemma, str):
            activity_by_lemma.setdefault(lemma.casefold(), []).append(state)
    for word in pack["vocabulary"]:
        matches = activity_by_lemma.get(word["lemma"].casefold(), [])
        if not matches:
            continue
        direct = states.get(word["id"], {})
        direct_exposures = direct.get("exposure_count", 0)
        exposures = direct_exposures + sum(item.get("exposure_count", 0) for item in matches)
        requests = (direct.get("dictionary_requests", direct.get("hint_requests", 0))
                    + sum(item.get("dictionary_requests", 0) for item in matches))
        weighted_mastery = direct.get("mastery", 0.0) * direct_exposures
        weighted_mastery += sum(item.get("mastery", 0.0) * item.get("exposure_count", 0)
                                for item in matches)
        reviews = [value for value in [direct.get("next_review"),
                   *(item.get("next_review") for item in matches)] if value]
        states[word["id"]] = {
            "exposure_count": exposures,
            "dictionary_requests": requests,
            "mastery": round(weighted_mastery / exposures, 4) if exposures else 0.0,
            "next_review": min(reviews, default=None),
        }
    return states


def _effective_difficulty(profile: dict[str, Any], variants: list[dict[str, Any]],
                          states: dict[str, dict[str, Any]]) -> tuple[int, str]:
    saved = profile["current_learner_difficulty"]["internal"]
    if len({variant["id"] for variant in variants}) < 2:
        return saved, "saved_level"
    vocabulary_ids = {word for variant in variants for word in variant["vocabulary_ids"]}
    exposures = sum(states.get(word, {}).get("exposure_count", 0) for word in vocabulary_ids)
    requests = sum(states.get(word, {}).get("dictionary_requests", 0) for word in vocabulary_ids)
    if exposures >= 3 and requests / exposures >= 0.5:
        return min(saved, 5), "frequent_dictionary_help"
    if exposures >= 3 and requests / exposures >= 0.25:
        return min(saved, 20), "some_dictionary_help"
    learning = profile.get("rom_learning", {})
    if learning.get("exposure_count", 0) >= 10 and learning.get("dictionary_rate", 0) >= 0.5:
        return min(saved, 20), "high_overall_dictionary_use"
    return saved, "saved_level"


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
    states = _combined_states(pack, profile)
    saved_difficulty = profile["current_learner_difficulty"]["internal"]
    difficulty, adaptation_reason = _effective_difficulty(profile, dialogue["variants"], states)
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
        "base_internal_difficulty": saved_difficulty,
        "effective_internal_difficulty": difficulty,
        "adaptation_reason": adaptation_reason,
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
