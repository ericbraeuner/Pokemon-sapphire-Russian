#!/usr/bin/env python3
"""Build a deterministic, wrapper-friendly vocabulary review queue."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import context_catalog


def _timestamp(value: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("review timestamps must be UTC ISO 8601 strings ending in Z")
    return datetime.fromisoformat(value[:-1] + "+00:00")


def _word_contexts(language: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for context_id, context in context_catalog.load().items():
        for word in context["words"][language]:
            result[word["id"]] = {
                "context_id": context_id,
                "context_kind": context["kind"],
                "source_id": context["source_id"],
            }
    return result


def build(profile: dict[str, Any], *, now: datetime | None = None,
          limit: int = 20, include_upcoming: bool = False) -> dict[str, Any]:
    if limit < 1:
        raise ValueError("limit must be at least 1")
    language = profile.get("selected_language")
    if language not in {"ru", "de"}:
        raise ValueError("profile selected_language must be ru or de")
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must include a timezone")
    now = now.astimezone(timezone.utc)
    contexts = _word_contexts(language)
    cards = []
    for word_id, state in profile.get("activity_vocabulary", {}).items():
        context = contexts.get(word_id)
        if context is None or state.get("next_review") is None:
            continue
        due_at = _timestamp(state["next_review"])
        is_due = due_at <= now
        if not is_due and not include_upcoming:
            continue
        seconds = int((now - due_at).total_seconds())
        cards.append({
            "word_id": word_id,
            "lemma": state["lemma"],
            "english_gloss": state["english_gloss"],
            **context,
            "due_at": state["next_review"],
            "is_due": is_due,
            "days_overdue": max(0, seconds // 86400),
            "mastery": state["mastery"],
            "exposure_count": state["exposure_count"],
            "dictionary_requests": state["dictionary_requests"],
            "srs_state": state["srs"]["state"],
        })
    cards.sort(key=lambda card: (
        not card["is_due"], card["due_at"], card["mastery"],
        -card["dictionary_requests"], card["word_id"],
    ))
    generated_at = now.isoformat().replace("+00:00", "Z")
    return {
        "schema_version": 1,
        "profile_id": profile.get("profile_id", ""),
        "selected_language": language,
        "cefr": profile["current_learner_difficulty"]["cefr"],
        "generated_at": generated_at,
        "due_count": sum(card["is_due"] for card in cards),
        "cards": cards[:limit],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", type=Path)
    parser.add_argument("--output", type=Path, help="write JSON instead of printing it")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--include-upcoming", action="store_true")
    parser.add_argument("--now", help="fixed UTC timestamp for testing or reproducible output")
    args = parser.parse_args()
    profile = json.loads(args.profile.read_text(encoding="utf-8"))
    now = _timestamp(args.now) if args.now else None
    rendered = json.dumps(
        build(profile, now=now, limit=args.limit, include_upcoming=args.include_upcoming),
        ensure_ascii=False, indent=2,
    ) + "\n"
    if args.output:
        temporary = args.output.with_suffix(args.output.suffix + ".tmp")
        temporary.write_text(rendered, encoding="utf-8")
        temporary.replace(args.output)
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
