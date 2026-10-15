#!/usr/bin/env python3
"""Resolve exported learner activity contexts to stable vocabulary records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import build_demo as demo
import field_dictionary
import opening

FIELD_CONTEXT_BASE = 0x1000


def _words(prefix: str, values: list[list[str]]) -> list[dict[str, str]]:
    return [
        {"id": f"{prefix}.{index}", "lemma": lemma, "english_gloss": gloss}
        for index, (lemma, gloss) in enumerate(values, 1)
    ]


def load() -> dict[int, dict[str, Any]]:
    contexts: dict[int, dict[str, Any]] = {}
    for context_id, entry in enumerate(opening.load()["dialogues"], 1):
        contexts[context_id] = {
            "kind": "authored_dialogue",
            "source_id": entry["id"],
            "source_symbol": entry["base_symbol"],
            "words": {
                tag: _words(f"opening.{entry['id']}.{tag}", entry["words"][tag])
                for tag in ("ru", "de")
            },
        }
    for index, (symbol, languages) in enumerate(field_dictionary.load().items()):
        context_id = FIELD_CONTEXT_BASE + index
        if context_id in contexts:
            raise ValueError(f"duplicate learner context: 0x{context_id:04X}")
        contexts[context_id] = {
            "kind": "field_dictionary",
            "source_id": symbol,
            "source_symbol": symbol,
            "words": {
                tag: _words(f"field.{symbol}.{tag}", languages[tag])
                for tag in ("ru", "de")
            },
        }
    ids = [word["id"] for context in contexts.values()
           for words in context["words"].values() for word in words]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate context vocabulary ID")
    return contexts


def serializable() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "contexts": {f"0x{context_id:04X}": value for context_id, value in load().items()},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="write JSON to this path instead of stdout")
    args = parser.parse_args()
    rendered = json.dumps(serializable(), ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
