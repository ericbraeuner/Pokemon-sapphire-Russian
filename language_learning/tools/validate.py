#!/usr/bin/env python3
"""Validate language-learning JSON data without third-party dependencies."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CEFR = {"A1", "A2", "B1", "B2", "C1", "C2"}
PACK_ID = re.compile(r"^[a-z0-9][a-z0-9._-]+$")


class ValidationError(Exception):
    pass


def load(path: Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as stream:
            value = json.load(stream)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"{path}: cannot load JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValidationError(f"{path}: root must be an object")
    return value


def require_keys(value: dict[str, Any], keys: set[str], where: str) -> None:
    missing = sorted(keys - value.keys())
    if missing:
        raise ValidationError(f"{where}: missing keys: {', '.join(missing)}")


def unique_ids(values: list[dict[str, Any]], where: str) -> set[str]:
    ids = [item.get("id") for item in values]
    if any(not isinstance(item_id, str) or not item_id for item_id in ids):
        raise ValidationError(f"{where}: every item needs a non-empty string id")
    if len(ids) != len(set(ids)):
        raise ValidationError(f"{where}: IDs must be unique")
    return set(ids)


def timestamp(value: Any, where: str) -> None:
    if value is None:
        return
    if not isinstance(value, str):
        raise ValidationError(f"{where}: timestamp must be a string or null")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError(f"{where}: invalid ISO 8601 timestamp") from exc


def validate_pack(path: Path, catalogue_ids: set[str]) -> str:
    pack = load(path)
    require_keys(pack, {"schema_version", "pack_id", "target_language", "character_requirements", "vocabulary", "grammar_notes", "dialogues"}, str(path))
    if pack["schema_version"] != 1 or not PACK_ID.fullmatch(pack["pack_id"]):
        raise ValidationError(f"{path}: unsupported schema_version or invalid pack_id")
    language = pack["target_language"]
    require_keys(language, {"tag", "name", "native_name"}, f"{path}: target_language")
    tag = language["tag"]
    if not isinstance(tag, str) or not tag:
        raise ValidationError(f"{path}: target language tag must be non-empty")
    chars = pack["character_requirements"]
    require_keys(chars, {"unicode_ranges", "rom_font_status"}, f"{path}: character_requirements")
    if chars["rom_font_status"] not in {"supported", "requires_font_work", "external_overlay_only"}:
        raise ValidationError(f"{path}: invalid rom_font_status")
    vocab_ids = unique_ids(pack["vocabulary"], f"{path}: vocabulary")
    grammar_ids = unique_ids(pack["grammar_notes"], f"{path}: grammar_notes")
    dialogue_ids: set[str] = set()
    for item in pack["vocabulary"]:
        require_keys(item, {"lemma", "english", "part_of_speech", "cefr", "first_introduction"}, f"{path}: vocabulary {item['id']}")
        if "dictionary_form" in item and (not isinstance(item["dictionary_form"], str) or not item["dictionary_form"].strip()):
            raise ValidationError(f"{path}: invalid dictionary_form for {item['id']}")
        if tag == "de" and item["part_of_speech"] == "noun" and not re.match(r"^(der|die|das) .+", item.get("dictionary_form", "")):
            raise ValidationError(f"{path}: German noun {item['id']} needs an article in dictionary_form")
        if item["cefr"] not in CEFR or item["first_introduction"] not in catalogue_ids:
            raise ValidationError(f"{path}: invalid CEFR or first_introduction for {item['id']}")
    for item in pack["grammar_notes"]:
        require_keys(item, {"title", "english_explanation", "cefr", "first_introduction"}, f"{path}: grammar {item['id']}")
        if item["cefr"] not in CEFR or item["first_introduction"] not in catalogue_ids:
            raise ValidationError(f"{path}: invalid CEFR or first_introduction for {item['id']}")
    for dialogue in pack["dialogues"]:
        require_keys(dialogue, {"dialogue_id", "variants"}, f"{path}: dialogue")
        dialogue_id = dialogue["dialogue_id"]
        if dialogue_id not in catalogue_ids or dialogue_id in dialogue_ids:
            raise ValidationError(f"{path}: unknown or duplicate dialogue_id {dialogue_id}")
        dialogue_ids.add(dialogue_id)
        variant_ids: set[str] = set()
        previous_difficulty = 0
        if not dialogue["variants"]:
            raise ValidationError(f"{path}: {dialogue_id} needs at least one variant")
        for variant in dialogue["variants"]:
            require_keys(variant, {"id", "text", "english_gloss", "cefr", "internal_difficulty", "vocabulary_ids", "grammar_note_ids"}, f"{path}: {dialogue_id} variant")
            if variant["id"] in variant_ids:
                raise ValidationError(f"{path}: duplicate variant {variant['id']}")
            variant_ids.add(variant["id"])
            difficulty = variant["internal_difficulty"]
            if variant["cefr"] not in CEFR or not isinstance(difficulty, int) or not 1 <= difficulty <= 100 or difficulty < previous_difficulty:
                raise ValidationError(f"{path}: invalid or unordered difficulty in variant {variant['id']}")
            previous_difficulty = difficulty
            unknown_vocab = set(variant["vocabulary_ids"]) - vocab_ids
            unknown_grammar = set(variant["grammar_note_ids"]) - grammar_ids
            if unknown_vocab or unknown_grammar:
                raise ValidationError(f"{path}: unresolved metadata reference in variant {variant['id']}")
    return tag


def validate_profile(path: Path, packs: dict[str, dict[str, set[str]]]) -> None:
    profile = load(path)
    require_keys(profile, {"schema_version", "profile_id", "selected_language", "current_learner_difficulty", "game_progress", "vocabulary", "grammar_exposure"}, str(path))
    if profile["schema_version"] != 1 or profile["selected_language"] not in packs:
        raise ValidationError(f"{path}: unsupported schema or language without a pack")
    difficulty = profile["current_learner_difficulty"]
    require_keys(difficulty, {"cefr", "internal"}, f"{path}: current_learner_difficulty")
    if difficulty["cefr"] not in CEFR or not isinstance(difficulty["internal"], int) or not 1 <= difficulty["internal"] <= 100:
        raise ValidationError(f"{path}: invalid learner difficulty")
    language = packs[profile["selected_language"]]
    for lemma_id, state in profile["vocabulary"].items():
        if lemma_id not in language["vocabulary"]:
            raise ValidationError(f"{path}: unknown vocabulary ID {lemma_id}")
        require_keys(state, {"mastery", "exposure_count", "hint_requests", "last_seen", "next_review", "srs"}, f"{path}: {lemma_id}")
        if not 0 <= state["mastery"] <= 1 or min(state["exposure_count"], state["hint_requests"]) < 0:
            raise ValidationError(f"{path}: invalid learning counters for {lemma_id}")
        timestamp(state["last_seen"], f"{path}: {lemma_id}.last_seen")
        timestamp(state["next_review"], f"{path}: {lemma_id}.next_review")
        require_keys(state["srs"], {"state", "interval_days", "ease", "lapses"}, f"{path}: {lemma_id}.srs")
        if state["srs"]["state"] not in {"new", "learning", "review", "relearning"}:
            raise ValidationError(f"{path}: invalid SRS state for {lemma_id}")
    for grammar_id, state in profile["grammar_exposure"].items():
        if grammar_id not in language["grammar"]:
            raise ValidationError(f"{path}: unknown grammar ID {grammar_id}")
        require_keys(state, {"exposure_count", "hint_requests", "last_seen"}, f"{path}: {grammar_id}")
        timestamp(state["last_seen"], f"{path}: {grammar_id}.last_seen")


def main() -> int:
    catalogue = load(ROOT / "integration" / "dialogue_catalog.json")
    catalogue_ids = unique_ids(catalogue.get("dialogues", []), "dialogue catalogue")
    validate_sources(catalogue)
    packs: dict[str, dict[str, set[str]]] = {}
    pack_paths = sorted((ROOT / "language_packs").glob("*/pack.json"))
    if not pack_paths:
        raise ValidationError("no language packs found")
    for path in pack_paths:
        tag = validate_pack(path, catalogue_ids)
        pack = load(path)
        if tag in packs:
            raise ValidationError(f"duplicate target language {tag}")
        packs[tag] = {
            "vocabulary": {item["id"] for item in pack["vocabulary"]},
            "grammar": {item["id"] for item in pack["grammar_notes"]},
        }
        print(f"validated language pack: {tag} ({path.relative_to(ROOT)})")
    profile_paths = sorted((ROOT / "profiles").glob("*.json"))
    for path in profile_paths:
        validate_profile(path, packs)
        print(f"validated learner profile: {path.relative_to(ROOT)}")
    print(f"validation passed: {len(catalogue_ids)} dialogue IDs, {len(pack_paths)} packs, {len(profile_paths)} profiles")
    return 0


def validate_sources(catalogue: dict[str, Any]) -> None:
    """Resolve connected entries; planned entries remain explicitly unconnected."""
    repo = ROOT.parent.resolve()
    for dialogue in catalogue.get("dialogues", []):
        source = dialogue.get("source", {})
        if source.get("kind") != "script_hook":
            continue
        for path_key, symbol_key in [("path", "symbol"), ("base_text_path", "base_text_symbol")]:
            require_keys(source, {path_key, symbol_key}, f"dialogue {dialogue['id']}")
            path = (repo / source[path_key]).resolve()
            if not path.is_relative_to(repo) or not path.is_file():
                raise ValidationError(f"{dialogue['id']}: missing or unsafe source path")
            pattern = rf"^{re.escape(source[symbol_key])}::?(?:\s|$)"
            if not re.search(pattern, path.read_text(encoding="utf-8"), re.MULTILINE):
                raise ValidationError(f"{dialogue['id']}: source symbol not found: {source[symbol_key]}")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValidationError as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
