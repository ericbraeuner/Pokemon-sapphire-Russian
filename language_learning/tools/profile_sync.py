#!/usr/bin/env python3
"""Merge a learner-ROM counter snapshot into an external learner profile."""

from __future__ import annotations

import argparse
import copy
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import context_catalog
import adaptive_plan
import learner_dashboard
import review_queue

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
    if snapshot["schema_version"] not in {1, 2} or snapshot["selected_language"] not in LANGUAGES:
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
        event_keys = {"sequence", "kind", "context", "delta", "captured_at"}
        if snapshot["schema_version"] == 2:
            event_keys |= {"selected_language", "cefr"}
        if not isinstance(event, dict) or set(event) != event_keys:
            raise ValueError("invalid activity event")
        if not isinstance(event["sequence"], int) or event["sequence"] <= previous_sequence:
            raise ValueError("activity event sequences must be strictly increasing")
        if event["kind"] not in {"exposure", "dictionary"}:
            raise ValueError("invalid activity event kind")
        if not isinstance(event["context"], int) or not 0 <= event["context"] <= 0xFFFF:
            raise ValueError("invalid activity event context")
        if not isinstance(event["delta"], int) or event["delta"] < 1:
            raise ValueError("invalid activity event delta")
        if event.get("selected_language", snapshot["selected_language"]) not in LANGUAGES:
            raise ValueError("invalid activity event language")
        if event.get("cefr", snapshot["cefr"]) not in LEVEL_INTERNAL:
            raise ValueError("invalid activity event CEFR level")
        _timestamp(event["captured_at"])
        previous_sequence = event["sequence"]


def _update_activity_state(state: dict[str, Any], kind: str, delta: int, seen_at: str) -> None:
    counter = "exposure_count" if kind == "exposure" else "dictionary_requests"
    state[counter] += delta
    exposures = state["exposure_count"]
    requests = state["dictionary_requests"]
    state["mastery"] = round(exposures / (exposures + 3 + 2 * requests), 4) if exposures else 0.0
    if kind == "dictionary":
        interval = 1
    else:
        successful_exposures = max(0, exposures - requests)
        interval = min(30, 2 ** max(0, min(5, successful_exposures - 1)))
    state["srs"] = {
        "state": "review" if state["mastery"] >= 0.6 else "learning",
        "interval_days": interval,
        "ease": round(max(1.3, 2.3 - requests * 0.1), 2),
        "lapses": state.get("srs", {}).get("lapses", 0),
    }
    seen = datetime.fromisoformat(seen_at[:-1] + "+00:00")
    state["last_seen"] = seen_at
    state["next_review"] = (seen + timedelta(days=interval)).isoformat().replace("+00:00", "Z")


def _authored_progress() -> dict[str, dict[str, Any]]:
    path = Path(__file__).resolve().parents[1] / "integration/dialogue_catalog.json"
    catalogue = json.loads(path.read_text(encoding="utf-8"))
    return {
        entry["source"]["authored_id"]: entry["progress"]
        for entry in catalogue["dialogues"]
        if entry["source"]["kind"] == "script_hook"
    }


def _advance_progress(profile: dict[str, Any], authored_id: str,
                      progress_by_id: dict[str, dict[str, Any]]) -> None:
    reached = progress_by_id.get(authored_id)
    if reached is None:
        return
    current = profile["game_progress"]
    if current["chapter"] == reached["chapter"]:
        current["sequence"] = max(current["sequence"], reached["sequence"])


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
    progress_by_id = _authored_progress()
    activity = result.setdefault("activity_vocabulary", {})
    cursors = dict(previous.get("event_cursors", {})) if previous else {}
    cursor = cursors.get(snapshot["session_id"], 0)
    for event in snapshot["events"]:
        if event["sequence"] <= cursor:
            continue
        context = catalogue.get(event["context"])
        if context is None:
            raise ValueError(f"unknown learner activity context: 0x{event['context']:04X}")
        if event["kind"] == "exposure" and context["kind"] == "authored_dialogue":
            _advance_progress(result, context["source_id"], progress_by_id)
        event_language = event.get("selected_language", snapshot["selected_language"])
        for word in context["words"][event_language]:
            state = activity.setdefault(word["id"], {
                "lemma": word["lemma"], "english_gloss": word["english_gloss"],
                "exposure_count": 0, "dictionary_requests": 0, "last_seen": None,
                "mastery": 0.0, "next_review": None,
                "srs": {"state": "new", "interval_days": 0, "ease": 2.3, "lapses": 0},
            })
            state.setdefault("mastery", 0.0)
            state.setdefault("next_review", None)
            state.setdefault("srs", {"state": "new", "interval_days": 0, "ease": 2.3, "lapses": 0})
            _update_activity_state(state, event["kind"], event["delta"], event["captured_at"])
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


def _write_json(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _write_text(path: Path, value: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(value, encoding="utf-8")
    temporary.replace(path)


def synchronize(profile_path: Path, snapshot_path: Path, *, allow_reset: bool = False,
                review_output: Path | None = None, review_limit: int = 20,
                include_upcoming: bool = False,
                dashboard_output: Path | None = None,
                variant_output: Path | None = None,
                runtime_output: Path | None = None) -> dict[str, Any]:
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    updated = merge(profile, snapshot, allow_reset=allow_reset)
    captured_at = _timestamp_value(snapshot["captured_at"])
    queue = None
    if review_output:
        queue = review_queue.build(
            updated, now=captured_at, limit=review_limit,
            include_upcoming=include_upcoming,
        )
    dashboard = (learner_dashboard.render(updated, now=captured_at, limit=review_limit)
                 if dashboard_output else None)
    plan = None
    if variant_output or runtime_output:
        tag = updated["selected_language"]
        pack = json.loads((Path(__file__).resolve().parents[1] / "language_packs" / tag / "pack.json").read_text(encoding="utf-8"))
        catalogue = json.loads(
            (Path(__file__).resolve().parents[1] / "integration/dialogue_catalog.json").read_text(encoding="utf-8")
        )
        plan = adaptive_plan.build(pack, updated, catalogue, now=captured_at)
    _write_json(profile_path, updated)
    if review_output and queue is not None:
        _write_json(review_output, queue)
    if dashboard_output and dashboard is not None:
        _write_text(dashboard_output, dashboard)
    if variant_output and plan is not None:
        _write_json(variant_output, plan)
    if runtime_output and plan is not None:
        _write_text(runtime_output, adaptive_plan.render_lua(plan))
    return updated


def _timestamp_value(value: str) -> datetime:
    _timestamp(value)
    return datetime.fromisoformat(value[:-1] + "+00:00")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", type=Path)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--allow-reset", action="store_true")
    parser.add_argument("--review-output", type=Path,
                        help="also write a wrapper-ready vocabulary review queue")
    parser.add_argument("--review-limit", type=int, default=20)
    parser.add_argument("--include-upcoming", action="store_true")
    parser.add_argument("--dashboard-output", type=Path,
                        help="also write a localized self-contained progress page")
    parser.add_argument("--variant-output", type=Path,
                        help="also write adaptive selections for unlocked dialogues")
    parser.add_argument("--runtime-output", type=Path,
                        help="also write the mGBA runtime selection table")
    args = parser.parse_args()
    synchronize(
        args.profile, args.snapshot, allow_reset=args.allow_reset,
        review_output=args.review_output, review_limit=args.review_limit,
        include_upcoming=args.include_upcoming, dashboard_output=args.dashboard_output,
        variant_output=args.variant_output, runtime_output=args.runtime_output,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
