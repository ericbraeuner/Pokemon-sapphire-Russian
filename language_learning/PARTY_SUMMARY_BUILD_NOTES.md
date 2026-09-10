# Party, summary, and item interface checkpoint — 2026-09-08

## What changed

- Party prompts, item-use messages, and Pokémon action menus now use the selected
  Russian or German language.
- Party move-name buffers reuse the shared learner battle-name catalogue.
- Summary page headings, stat labels, held items, move names, all 25 natures,
  all 77 Generation III abilities, and trainer-memo fragments now use learner translations.
- Trainer-memo locations reuse the complete learner map-name catalogue.
- The labels formerly baked into the English summary artwork are regenerated at
  build time for Russian and German. This covers profile, ability, trainer origin,
  item, ribbon, stats, experience, moves, and description labels without committing
  generated bitmap or binary files.
- The shared item catalogue grew from 23 to 47 items. The new group covers drinks,
  herbal medicine, PP medicine, vitamins, and common in-battle stat items. Bag,
  shop, field-item, and held-item displays all reuse these names.

## Verification

- All 39 language-learning tests pass, including the 88-pixel item-name and
  two-line 104-pixel item-description limits.
- Both the learner build and the ordinary Sapphire build compile successfully.
- Russian party/action screens and Russian and German summary pages were inspected
  in the emulator. Page headings, nature, starter ability, early move names,
  held-item text, stats, encounter location, and embedded labels all changed with
  the saved language.
- Emulator saves, screenshots, generated assembly, ROMs, maps, objects, and compiler
  binaries remain local ignored build artifacts and are not part of this checkpoint.

## Remaining Phase 3 work

- Complete remaining Bag, Pokédex, settings, and item-use edge cases, followed
  by another exhaustive Russian/German visual pass.

## Options, save, and Bag follow-up — 2026-09-08

- Added Russian and German text for every Options-screen heading and choice,
  including text speed, battle animation/style, sound, button mode, window frame,
  and cancel.
- Save-summary labels now explicitly use the learner language alongside the
  already localized map name.
- Bag action menus now translate their delayed-draw and in-battle paths as well as
  the ordinary field menu. This closes several routes where Use, Give, Toss,
  Register, Check, Confirm, and Cancel could still appear in English.
- Added an automated test that guards all 21 Options entries, the four save labels,
  and the previously missed Bag action paths. Both learner and stock builds pass.

## Item-use follow-up — 2026-09-09

- Added reusable Russian and German labels for walking, checking an item, and
  starting TM/HM machines.
- Added bounded templates for the Coin Case total, TM/HM move-teaching question,
  and recovery from confusion. Runtime coin totals, move names, and Pokémon names
  remain intact in both languages.
- Expanded the automated placeholder checks to cover these item-use messages.

## Complete ability catalogue — 2026-09-09

- Expanded the summary catalogue from 25 common abilities to every one of the 77
  abilities supported by Pokémon Sapphire.
- Every ability now has a bounded Russian and German name and description; German
  names follow the game's existing German terminology.
- The summary screen keeps the original English tables as its non-learner fallback,
  so ordinary Sapphire builds remain unchanged.

## Save, Safari, and unseen Pokédex states — 2026-09-09

- Added Russian and German emergency-save and full-screen saving messages.
- The Safari Zone stock window now preserves and displays the live ball count in
  the selected learner language.
- Unknown Pokédex species, height, and weight placeholders no longer expose English
  words or imperial-unit fragments before the Pokémon has been identified.
- Latin A–Z search ranges remain unchanged because Sapphire's search engine still
  groups entries by their internal international names; relabeling those ranges as
  Cyrillic would make the visible filter inaccurate.

## Extended shared battle flows — 2026-09-09

- Expanded the bilingual battle catalogue from 85 to 133 templates.
- Added double-battle introductions and send-out/withdrawal/results, Poké Ball
  failure messages, caught-Pokémon nickname/PC/Pokédex follow-up, weather, status
  cures, held-item recovery, and evolution start/completion/cancellation text.
- Runtime trainer names, Pokémon names, move names, items, and sound/control tokens
  remain in their original positions. Automated tests now verify representative
  placeholders and the flee sound token in both languages.

## Phase 3 shared-interface completion — 2026-09-09

- Added 27 party, item-effect, held-item, move-learning, shop, and storage
  templates. Live Pokémon names, move names, item names, quantities, prices,
  levels, and stat names remain runtime values rather than baked-in examples.
- Translated the four egg-status descriptions and the remaining compact party
  stat, shop-delivery, PP-restoration, and box labels.
- Preserved the complete animated move-forgetting sequence: all timed pauses,
  the ball-bounce sound, page changes, and runtime Pokémon/move placeholders.
- Replaced the shop and selling window's embedded MONEY sprite with generated
  Russian `ДЕНЬГИ` and German `GELD` artwork. The original 32-by-16 sprite size,
  palette, and surrounding interface remain unchanged.
- The Phase 3 source audit now checks Bag/item use, Pokédex, start/save menus,
  party/summary, Pokémon storage, and shops. Its only untranslated symbols are
  explicitly classified punctuation, formatting sentinels, or runtime player
  data.

## Verification

- All 43 language-learning tests pass, including text-box and buffer bounds,
  control-code preservation, exact money-sprite dimensions, and the exhaustive
  Phase 3 symbol audit.
- Learner and ordinary Sapphire configurations both compile successfully.
- Generated Russian and German MONEY sprites were inspected directly. A full
  emulator traversal of every newly translated edge case remains the next
  hands-on QA pass; it should use a disposable copy of the player's save.
- ROMs, ELF/map files, generated assembly, objects, screenshots, and saves remain
  ignored local outputs and must not enter the source commit.

## Stock-isolation follow-up — 2026-09-09

- Moved the Options screen's translated-text buffer wholly behind `LEARNER_DEMO`.
  The ordinary build again uses the original 15-byte local buffer and draw path.
- Preserved both original held-item name paths in the ordinary summary screen while
  keeping their shared learner translation path in Russian and German.
- Added source-level regression checks for both isolation boundaries.
- All 43 language-learning tests and the learner build pass. `make
  compare_sapphire` now succeeds against stock SHA-1
  `3ccbbd45f8553c36463f13b938e833f652b793e4`.
- `PHASE3_QA_CHECKLIST.md` defines the remaining disposable-save emulator matrix.

## Emulator boot smoke test — 2026-09-09

- Downloaded the official portable mGBA 0.10.5 release into the ignored `build`
  directory; the emulator itself is not part of the repository.
- Copied the learner ROM into an isolated ignored directory and ran it under the
  SDL frontend for ten seconds. The emulator stayed alive without a startup crash.
- The isolated ROM retained SHA-256
  `e7defeb2059aa25c068471c153cf6b8ac358c9b68c180f6731caa5cd94cb4a6e`.
- The smoke test did not load, copy or write either real repository save. Full
  Russian/German screen traversal still requires the visual checklist because
  stable mGBA 0.10.5 does not expose its Lua scripting interface on the command line.

## Automated visual follow-up — 2026-09-09

- Used the official mGBA development build's command-line Lua support with isolated
  ROM and save copies to capture setup, Birch, start menu, Pokédex, party, Bag,
  save and Options screens.
- Verified Russian A1 with English help and German C2 without help reach Birch in
  the selected language. The existing learner save remained byte-for-byte unchanged.
- The screenshots exposed an English `CANCEL` graphic in the party screen. Added a
  generated Russian `Назад` / German `Zurück` version behind `LEARNER_DEMO` while
  preserving the original stock sheet.

## Common battle-state follow-up — 2026-09-09

- Expanded the bilingual battle catalogue from 133 to 164 shared templates.
- Added common sleep, poison, paralysis, confusion, freezing, healing, PP,
  recharge, stat-limit, move-failure and charging messages used across wild,
  trainer, rival and later battles.
- Kept Pokémon, move, item and stat names as runtime placeholders so the same
  translations work throughout the game instead of baking in early-game examples.
- Added a second group of 36 templates for disabled moves, Encore, attraction,
  recoil, protection, Safeguard, Mist, sun, rain, sandstorm, hail and Spikes,
  bringing shared battle coverage to 200 templates.
- Added 36 more templates for ability-based status prevention, trapping, Leech
  Seed, Nightmare, Curse, Perish Song, Substitute and Endure. Shared battle
  coverage now reaches 236 of the engine's 479 message templates.
- Added 38 stat-change, type-change, targeting, stored-energy, sleep and
  health-drain templates. The shared bilingual battle catalogue now covers 274
  of 479 engine messages.
- Added 42 move-learning, move-charge, status, escape, multi-hit, Uproar and
  delayed-effect templates. Shared battle coverage now reaches 316 of 479
  engine messages.
- Added 51 held-item, ability, escape, switching, Wish, Grudge, Taunt, Torment,
  sealing and reflected-move templates. Shared battle coverage now reaches 367
  of 479 engine messages.
- Extended the battle compiler to preserve native sound, music, Pokéblock,
  palette, highlight and alignment controls in translated messages.
- Added the remaining 89 user-visible battle, catching, disobedience, Safari,
  move-forgetting, status, stat and move-type strings. The catalogue now covers
  456 of 479 engine symbols; an exhaustive test limits the 23 omissions to empty,
  punctuation, formatting and internal sentence-composition fragments.
- Added a conservative 200-pixel literal-line guard to the battle compiler and
  shortened or reflowed 16 German messages it identified, including Safari,
  Wally, weather, move-forgetting and ability text. This prevents those known
  strings from reaching a ROM wider than the message area.

## Shared move-name expansion — 2026-09-09

- Expanded the reusable bilingual move catalogue from 21 to 62 moves, covering
  the early universal physical, punch, kick, sound, trapping and status moves.
- Kept the German labels aligned with established German move terminology while
  shortening labels where Sapphire's 72-pixel battle field requires it. Russian
  names use compact, readable equivalents under the same limit.
- Battle messages, party screens and summary pages all reuse this catalogue, so
  these names no longer need separate translations in each interface.
- Added regression coverage for the catalogue size, representative move hooks
  and the existing per-language width validation.

## Elemental move-name expansion — 2026-09-09

- Expanded the shared catalogue again, from 62 to 99 moves. This batch covers
  Fire, Water, Ice, Electric, Grass, Rock, Ground and Psychic attacks plus their
  common powder and field-move companions.
- Kept familiar German move terminology in compact forms and added matching
  Russian labels. Every entry passes the same 72-pixel battle-name limit.
- Added representative source-hook checks for Surf, Ice Beam, Earthquake and
  Psychic so the new names remain connected to the runtime translation table.

## Status and defensive move-name expansion — 2026-09-09

- Expanded shared coverage from 99 to 137 moves with Psychic/status techniques,
  screens and defensive effects, healing, self-destruction, and common special
  attacks from the original move set.
- Added source-hook checks for Hypnosis, Recover, Light Screen and Self-Destruct.
  All Russian and German labels remain subject to the 72-pixel compile-time guard.

## Late Generation I move-name expansion — 2026-09-09

- Expanded shared coverage from 137 to 182 moves, completing the remaining
  Generation I move constants and continuing through the first 15 Generation II
  techniques.
- This batch includes transformation, recovery, trapping, recoil, sleep, poison,
  copying and field techniques used by a wide range of later opponents.
- Added representative hooks for Dream Eater, Transform, Rest, Substitute and
  Aeroblast while retaining compile-time Russian/German width validation.

## Generation II system move-name expansion — 2026-09-09

- Expanded shared coverage from 182 to 227 moves, adding 45 Generation II
  techniques including Protect, Spikes, Sandstorm, Baton Pass, weather-adjacent
  effects, priority attacks, recovery, hazards and Dark/Steel attacks.
- Added representative runtime-table checks for Protect, Spikes, Sandstorm and
  Baton Pass. The complete catalogue remains pixel-width checked in both languages.

## Late Generation II and early Hoenn move names — 2026-09-09

- Expanded shared coverage from 227 to 271 moves. The 44-name batch completes
  Generation II and adds early Generation III weather, recovery, recoil, Dark,
  Steel, Ghost and team-support techniques.
- Added representative runtime hooks for Iron Tail, Rain Dance, Shadow Ball and
  Helping Hand while retaining complete bilingual pixel-width validation.
