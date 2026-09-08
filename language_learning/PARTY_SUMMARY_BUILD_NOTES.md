# Party, summary, and item interface checkpoint — 2026-09-08

## What changed

- Party prompts, item-use messages, and Pokémon action menus now use the selected
  Russian or German language.
- Party move-name buffers reuse the shared learner battle-name catalogue.
- Summary page headings, stat labels, held items, move names, all 25 natures,
  starter abilities, and trainer-memo fragments now use learner translations.
- Trainer-memo locations reuse the complete learner map-name catalogue.
- The labels formerly baked into the English summary artwork are regenerated at
  build time for Russian and German. This covers profile, ability, trainer origin,
  item, ribbon, stats, experience, moves, and description labels without committing
  generated bitmap or binary files.
- The shared item catalogue grew from 23 to 47 items. The new group covers drinks,
  herbal medicine, PP medicine, vitamins, and common in-battle stat items. Bag,
  shop, field-item, and held-item displays all reuse these names.

## Verification

- All 38 language-learning tests pass, including the 88-pixel item-name and
  two-line 104-pixel item-description limits.
- Both the learner build and the ordinary Sapphire build compile successfully.
- Russian party/action screens and Russian and German summary pages were inspected
  in the emulator. Page headings, nature, starter ability, early move names,
  held-item text, stats, encounter location, and embedded labels all changed with
  the saved language.
- Emulator saves, screenshots, generated assembly, ROMs, maps, objects, and compiler
  binaries remain local ignored build artifacts and are not part of this checkpoint.

## Remaining Phase 3 work

- Expand ability names and descriptions beyond the three starter abilities.
- Complete remaining Bag, Pokédex, Save/settings, and item-use edge cases, followed
  by another exhaustive Russian/German visual pass.
