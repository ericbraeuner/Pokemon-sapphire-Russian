# Language-learning framework

This directory contains data contracts and integration seams for turning a base
Pokemon game into an adaptive language-learning experience. It is deliberately
separate from the normal ROM build. An optional playable build translates Birch and 57 field dialogue entries in Russian and German,
with saved language/level choices, translated help menus, and dictionary help. See [PLAY_DEMO.md](PLAY_DEMO.md) for beginner-friendly instructions.

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

`tools/adaptive_selector.py` implements this contract for external wrappers. It
rejects variants above the selected internal difficulty or ahead of game
progress, enforces each variant's new-word budget, and selects the hardest
eligible variant. Due vocabulary and known-word mastery break ties without ever
changing the learner's selected CEFR level.
Context-specific gameplay records are matched back to stable pack vocabulary by
their lemma. After at least three relevant exposures, repeated dictionary use
can temporarily select A2 or A1 wording below the saved level. A high overall
help rate can conservatively select A2 after ten exposures. The saved difficulty
remains the ceiling and is never changed by this adjustment. Every selection
records both difficulty values and its reason so a wrapper can explain the choice.

The adaptive packs now cover 298 authored early-game scenes: arriving
in town, Mom's welcome and moving instructions, the room reminder, setting the
clock, inspecting the finished room, and the complete introductory TV sequence
through Mom's next-door direction. Coverage also includes the bedroom GameCube,
notebook, bookshelf, picture books, home computer and school email, ordinary TV
programs, the neighbor-family conversations, both May and Brendan introduction
branches, and the first three Professor Birch laboratory conversations. Scenes
whose authored wording changes by difficulty provide A1, A2, and natural B1
variants in both Russian and German; short lines whose wording is identical
across levels use one honest shared variant. Littleroot's outdoor residents,
grass and rescue warnings, post-rescue encouragement, town sign, laboratory sign,
and both house signs are included as well. Route 101 now contributes the wall-map
lead-in, Birch's complete rescue sequence, both route residents, and its actual
northbound sign; the former route-sign placeholder is now connected to the real
script and text symbol. The original welcome example retains its two established
variants. Birch's starter gift and follow-up guidance, Mom's Running Shoes lesson,
and both May and Brendan Route 103 research and battle-challenge branches are now
part of the adaptive catalogue too. German noun records include their articles.
The Route 103 victory responses, Pokédex explanation, May and Brendan Poké Ball
handoffs, and every authored Oldale interaction now follow the same adaptive
contract. Wally's Petalburg Gym introduction, request for a Pokémon, borrowed
Pokémon and Poké Ball handoff, invitation, Route 102 catching demonstration,
return, and Norman's next objective now use adaptive A1, A2, and natural wording.
Route 102's two residents and both directional signs follow the same adaptive
contract. Its four first-battle trainers, Calvin's rematch, their defeat lines,
and their post-battle comments now use the trainer bridge as well. Route 104
continues the progression through residents, directional signs, the flower-shop
sign, and early trainer tips. Battle and event progression remain unchanged.
Petalburg Woods now adds its complete Devon researcher encounter,
Team Aqua confrontation, reward and warning sequence, both local residents,
held-item guidance, trainer-tip signs, and every local trainer line. Route 104
coverage also includes both roadside item gifts and follow-up advice,
plus the flower shop's welcome, Berry lesson, watering instructions, daily gift,
Wailmer Pail handoff, and Berry-use guidance. Automated coverage requires the
adaptive catalogue to resolve every
source symbol in `opening.json`, including the clock reminder that was initially
missed. The mGBA runtime bridge can apply these selections to the compiled ROM
variants while preserving the saved CEFR fallback when the bridge is absent.
Rustboro's first-arrival coverage now includes every outdoor resident and child,
the Gym and Trainer School guidance, Mr. Briney directions, evolution and trade
lessons, and all seven city, building, school, Gym, and tunnel signs. Inside the
Trainer School, the blackboard and its five status lessons, Quick Claw handoff,
held-item explanations, student conversations, trade example, and notebook now
use the same three adaptive text bands.
Rustboro's next indoor batch adds Cutter's House, the nickname and Trainer
School homes, both apartment buildings, the Poké Mart shoppers, and all three
ordinary Pokémon Center visitors. These conversations cover Cut and HMs,
abilities, nicknames, Devon history, useful shopping advice, Pokémon
personalities, and 24 contextual vocabulary introductions.
Rustboro's Gym and trade-house batch adds all Gym advice, both junior trainers,
Roxanne's challenge and defeat, the Stone Badge and TM39 explanations, the Gym
statues, and the trade-house follow-up conversations. Trainer introductions and
defeat lines use the translation bridge so their battle timing remains intact.
The first Devon story batch covers every lobby state plus the guided walk to
Mr. Stone, his two delivery requests, the PokéNav gift and explanation, and his
follow-up reminder. The item fanfare message uses adaptive translation without
changing its original wait and fanfare sequence.
Devon's second batch completes the research floor, including Poké Ball and
PokéNav development, dream research, every fossil-restoration state, the
restored Pokémon handoff, Mr. Stone's EXP Share reward, the Slateport reminder,
and the rare-rock display. Choice and fanfare messages keep their native flow.
Route 116 coverage begins with the tunnel worker's three story states, both
route and tunnel signs, the workers' rest-house sign, and the evolution and
Bag Trainer Tips signs.
Trainer introductions and defeat lines can now opt into the same generated
variant table. The battle setup records the introduction context before the
encounter and switches to the defeat context when combat begins, leaving the
trainer command, encounter, result, and rematch machinery untouched.

`tools/adaptive_plan.py` evaluates the entire unlocked catalogue at once and
writes a wrapper-ready plan containing the chosen text, source symbol, vocabulary,
and selection metrics for each scene. A fully progressed early-game profile gets
one selection for every authored scene; earlier profiles receive only scenes
allowed by their current chapter and sequence.

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

`integration/dialogue_catalog.json` connects all 298 authored lessons to their
real script hooks and original text symbols, including the shared moving-in
scripts and Route 101 sign. Validation checks both ends of every connection.
The normal game dialogue follows the extra lesson; important story instructions
are not replaced.

`tools/build_demo.py` and `tools/opening.py` generate ignored assembly.
`opening.json` currently holds 298 source-symbol mappings,
translations in three text bands, English help, and dictionary entries. This
prototype bundle is validated during generation and tests; it is separate from
the original language-pack/profile schema and does not update external profiles.

Language, CEFR level, mode, the active/requested dialogue dictionary, and two
saturating learning counters use reserved persistent variables 0x40F0–0x40F6.
New-game setup runs before Birch. Pending choices live in a dedicated four-byte
EWRAM allocation until NewGameInitData finishes clearing save variables, then
are copied once into those variables. Continue does not run setup or reset them.
They do not change save size and are written with the normal game save. Only
the learner build reads/writes them. Always keep experimental saves separate.
During an authored learning dialogue, R requests the active dictionary. The
generated script shows the correct Russian or German entries and then replays
the interrupted page. Text without curated vocabulary remains unaffected.
`field_dictionary.json` extends the same behavior to 160 item, shop, PC, mail,
Secret Base, Abandoned Ship, Dewford, Granite Cave, Slateport, and field messages. Its central wait handler shows the glossary,
replays the original message with its live names and quantities, and then resumes
the original event script. Each entry receives a stable context in the range
`0x1000`–`0x109F`, following its append-only catalogue order; do not reorder
existing entries when adding vocabulary.
`tools/context_catalog.py` resolves those IDs and all authored-dialogue IDs
to stable, language-specific vocabulary records. It can print the live catalogue
or write it with `--output`; generated copies remain build artifacts rather than
committed duplicate data.
Each authored target-language page, curated field or item message, and dictionary
opening increments its own saved counter. Replaying a message after dictionary
help does not count it twice. Both counters stop at 65,535 instead of wrapping to zero. An emulator
wrapper can export those values as a small JSON snapshot; `tools/profile_sync.py`
validates and atomically merges it into the matching external profile, including
language, CEFR level, totals, dictionary-use rate, and the most recent dialogue
contexts responsible for an exposure and dictionary request. Counter regressions are
rejected unless the wrapper explicitly identifies a reset or rewound save. These
metrics do not automatically change difficulty yet.

The wrapper snapshot contract is in `schemas/rom-learning-snapshot.schema.json`.
To merge a captured snapshot without partially rewriting a profile, run:

```sh
python language_learning/tools/profile_sync.py language_learning/profiles/sample-learner.json snapshot.json
```

Pass `--review-output review-queue.json` to update the external profile and emit
its currently due review cards in the same synchronization step. Add
`--include-upcoming` when the wrapper also needs the future schedule. Pass
`--dashboard-output learner-progress.html` to refresh the localized progress page
from the same captured emulator state. Pass `--variant-output adaptive-plan.json`
to refresh all currently unlocked adaptive dialogue selections from that same
snapshot. Pass `--runtime-output adaptive-runtime.lua` to also create the compact
table that mGBA can apply while the game is running. The session watcher accepts
the same options, so language, level,
mastery, and review changes are reflected without a separate command.
Exposure to an authored scene also advances the external profile's sequence to
that scene's stable catalogue position without moving it backwards. Consequently,
later synchronized plans unlock as the player reaches them; dictionary requests
and ordinary field-message exposures do not falsely advance story progress.

Use `--allow-reset` only when intentionally starting over or synchronizing a
rewound save whose counters are lower than the profile's last snapshot.

For mGBA 0.10 or newer, load `mgba/export_learner_snapshot.lua` from
**Tools > Scripting**. It reads the learner build's reserved variables continuously,
writes only when values change, and also reacts to emulator start and save-data
updates. It observes every frame so it can retain an ordered event
for each counter change; profile synchronization uses a per-session cursor to
ignore events it has already imported. Set `OUTPUT_PATH` and `SOURCE_ID` at the top of the script for
the profile and save being used. Released mGBA builds do not reliably support a
command-line script-loading option, so loading it from the Scripting window is
currently a manual step. The exporter only reads emulated memory.
Snapshot replacement keeps a temporary backup until the new JSON file is safely
installed, so a failed rename leaves the last valid snapshot available to the
session watcher.
Snapshot version 2 records language and CEFR on every event. If the player changes
settings between syncs, earlier Russian activity stays Russian and earlier German
activity stays German. The importer continues to accept version-1 snapshots by
using their top-level language and CEFR for legacy events.

To apply adaptive selections in the game, set `PLAN_PATH` near the top of
`mgba/apply_adaptive_plan.lua` to the generated `adaptive-runtime.lua`, then load
the script through **Tools > Scripting**. It watches the current authored-dialogue
context and writes only the reserved adaptive-variant variable. The selected
variant is one of the three versions already compiled into the ROM: A1, A2, or
natural. If the plan is missing, does not contain that scene, or the loader is not
running, the game keeps using the CEFR level saved in its normal settings.

On Windows, the setup helper removes the manual path editing and creates a
single mGBA launcher plus a double-clickable synchronizer:

```sh
python language_learning/tools/setup_mgba_runtime.py language_learning/profiles/sample-learner.json
```

Open `build/learner_runtime/start_learner_sync.cmd`, then load only
`build/learner_runtime/learner_runtime.lua` through mGBA's Scripting window.
The generated folder also receives the snapshot, adaptive plan, review queue,
and progress dashboard. It is an ignored local runtime folder, not source that
should be committed.

The learner build replaces the redundant `Exit` row in the ordinary START menu
(START or B still closes it) with a localized Learning page. That page reads the
saved language, CEFR level, introductory-help choice, exposure count, and
dictionary count directly from the reserved variables. It does not modify those
settings until the player uses left/right on the first three rows. Language,
CEFR level, and introductory help can then be changed; the two activity counters
remain read-only. Changes use the same reserved variables and persist with the
next ordinary in-game save. No save structure is added.
Imported events also update a conservative mastery estimate and next-review date
for every vocabulary record in the context. Dictionary use shortens the review
interval; repeated exposure gradually lengthens it up to 30 days. This activity
model provides recommendations only and never changes the player's selected
CEFR level.

`tools/review_queue.py` turns those recommendations into a stable JSON queue for
an emulator wrapper or future handheld review screen. By default it returns only
due words; `--include-upcoming` also returns scheduled words, and `--limit`
controls the number of cards. Each card retains its dialogue or field-message
context so a review UI can replay vocabulary in the place where it was learned:

```sh
python language_learning/tools/review_queue.py language_learning/profiles/sample-learner.json --include-upcoming
```

`tools/learner_dashboard.py` renders the same data as a self-contained, responsive
Russian or German progress page. It needs no server and does not modify the ROM
or save. This gives desktop, tablet, and handheld wrappers a usable interface
while direct in-game profile loading is still under development:

```sh
python language_learning/tools/learner_dashboard.py language_learning/profiles/sample-learner.json build/learner-dashboard.html
```

For normal play, `tools/session_watcher.py` watches the atomic JSON file written
by the mGBA script and refreshes the profile, review queue, and dashboard whenever
gameplay counters change. It retries incomplete or temporarily unavailable input
instead of corrupting the last good profile:

```sh
python language_learning/tools/session_watcher.py language_learning/profiles/sample-learner.json learner-snapshot.json --review-output build/review-queue.json --dashboard-output build/learner-dashboard.html
```

The font contains all 66 Russian letters in otherwise unused Latin slots.
A generated byte-to-glyph table preserves existing Latin character codes.
Capitals share the lowercase baseline, and ё uses the same body as е.
The charmap and original font assets are untouched. The generator rejects
unknown characters and control injection, splits messages to fit the 256-byte
buffer, and uses the native shadowed font for page arrows. Semicolons use a
corrected font-0 glyph, with font switching for German text; `; ` retains its space.
German noun entries can use `dictionary_form`
to include articles without changing lemma identity or fixed phrases.

`LEARNER_DEMO=1` produces `pokesapphire_learner.gba` with a separate object
directory, only for English Sapphire 1.0. Normal Sapphire remains a matching
build. Never commit ROMs, generated assembly, saves, or compiler binaries.

`ui.json` and `tools/ui.py` compile bounded native text for Birch, setup menus,
and the clock. `include/learner.h` declares those symbols. The clock reads saved
settings without modifying them. All C hooks are conditional on LEARNER_DEMO.

See PLAY_DEMO.md for the explicit coverage limits and full-immersion roadmap.

`ui_sources.json` is a whitelist of fixed source strings and their translations.
The text renderer and placeholder expansion resolve only exact source pointers;
unknown text and player-entered names pass through unchanged. Width measurement
uses the same translation as rendering. Each entry has a pixel width and line
limit checked during generation. PC labels fit existing windows without resizing.
`map_names.json` covers 88 map sections. Popups and the wall map render these
strings directly from ROM, avoiding the original 20-byte map-name buffers.
`graphic_labels.json` also supplies Russian and German text for the 23 shared
type/category badges on the Pokémon Summary screen. The generator preserves
their 32×16 sprite layout and border; the learner build chooses the sheet for
the saved language, while the normal build retains the original English sheet.
The same data now supplies the seven 32×8 status badges shared by Party and
Summary. Battle health boxes use separate art; their five status badges are
generated from the same language labels while leaving HP bars and the other
health-box tiles unchanged.
No save fields or structures changed in this update. Interface wording is shared
across difficulty levels; it does not claim six independently authored CEFR versions.

`battle.json` and `tools/battle.py` add battle-specific templates to that pointer
lookup. Battle `{STRING n}` tokens are deliberately distinct from field variables.
Templates retain pause/fanfare controls; stat and prefix fragments have no font
wrappers. The battle expander restores the selected font after inserted names.
`battle_names.json` maps early move/type constants to ROM strings using their
original array strides. Rendered translations never replace the engine's small
move-name buffers or stored nicknames. Unknown pointers still use original text.
Battle messages and interface wording currently share text across CEFR levels;
there is no in-battle dictionary shortcut yet.

`field_templates.json` is separate from battle templates: its small whitelist of
field placeholders preserves shop item, quantity and total price. The compiler
checks conservative expanded widths/buffer budgets and restores the language font
after each inserted value. Oldale NPCs use normal lesson help menus; shared nurse
and clerk text uses direct pointer translation so Yes/No results are not consumed
by a lesson menu. Shop item translations are scoped to the shop's large string
buffers; `CopyItemName` and saved item records remain unchanged.

## Adding data

Copy an existing language-pack directory, use a BCP 47 language tag, keep stable
dialogue and lemma IDs, and validate. Add catalogue entries only when their base
source location is known. Never embed learner-specific state in a language pack.
