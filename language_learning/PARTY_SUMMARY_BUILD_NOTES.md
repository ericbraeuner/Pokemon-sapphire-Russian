# Party, summary, and item interface checkpoint — 2026-09-08

## What changed

- Party prompts, item-use messages, and Pokémon action menus now use the selected
  Russian or German language.
- Party move-name buffers reuse the shared learner battle-name catalogue.
- Summary page headings, stat labels, held items, move names, all 25 natures,
  25 early-game abilities, and trainer-memo fragments now use learner translations.
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

- Expand ability names and descriptions beyond the 25 early-game abilities.
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
