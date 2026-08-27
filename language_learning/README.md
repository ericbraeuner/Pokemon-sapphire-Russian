# Language-learning framework

This directory contains data contracts and integration seams for turning a base
Pokemon game into an adaptive language-learning experience. It is deliberately
separate from the ROM today: no dialogue, gameplay, font, or charmap is changed.

## Architecture

The framework has four layers:

1. `integration/dialogue_catalog.json` assigns stable, language-neutral IDs to
   base-game text locations. Future extraction/insertion tools should use these
   IDs rather than source line numbers.
2. `language_packs/<language>/pack.json` supplies translations, English glosses,
   vocabulary, grammar, difficulty variants, and character requirements.
3. `profiles/*.json` stores per-learner state outside the ROM. An emulator
   wrapper can update these files without changing save data or ROM contents.
4. `tools/validate.py` checks schemas, references, uniqueness, and progression
   invariants. Run `make -f language_learning/Makefile validate` from the repo root.

The JSON Schemas in `schemas/` are the public machine-readable contracts. The
validator intentionally uses only Python's standard library so it can run in a
minimal toolchain.

## Adaptive progression

Each dialogue may have several variants. A future selector should first cap the
available variants by game progress, then choose the hardest variant compatible
with the learner's current difficulty and mastery. Selection should favor mostly
known lemmas, admit a small controlled number of new lemmas, and boost items due
for SRS review. Repeated encounters deliberately recycle vocabulary. Grammar
targets progress independently and can be gated by both prior exposure and game
progress.

The CEFR labels (`A1`, `A2`, `B1`, and later levels) are broad reporting labels;
`internal_difficulty` is the finer-grained ordering key. Profiles keep both game
progress and learner difficulty because neither is a safe proxy for the other.

## Emulator/wrapper contract

A future mGBA or Raspberry Pi wrapper is expected to:

- observe a source location and resolve its stable dialogue ID;
- choose a language-pack variant and display its text;
- show English gloss, vocabulary, and grammar help on demand;
- record exposures and hint requests in the learner profile;
- update `last_seen`, `next_review`, and SRS state;
- load one external profile per learner and expose progress in a handheld UI.

The wrapper should treat pack data as read-only and profile data as mutable.
Timestamps are UTC ISO 8601 strings. New integrations should preserve unknown
fields to allow schema evolution.

## Build and font integration points

`integration/dialogue_catalog.json` contains future extraction/insertion source
coordinates. A later generator may emit ROM-native text from the selected pack,
but generated output must remain a build artifact. Each pack declares required
Unicode ranges and a `rom_font_status`; validators and future build tooling can
refuse insertion until the base charmap/font supports those characters.

The current Russian example is intentionally `external_overlay_only`, so its
Cyrillic content is suitable for an emulator overlay but cannot enter the ROM.
No font or charmap work is included in this scaffold.

## Adding data

Copy an existing language-pack directory, use a BCP 47 language tag, keep stable
dialogue and lemma IDs, and validate. Add catalogue entries only when their base
source location is known. Never embed learner-specific state in a language pack.
