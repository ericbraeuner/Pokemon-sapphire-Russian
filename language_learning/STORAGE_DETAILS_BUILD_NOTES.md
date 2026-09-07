# Pokémon storage details — 2026-09-07

## Completed

- Localized the shared detailed storage actions, wallpaper categories, prompts,
  warnings, and release/deposit messages for Russian and German.
- Localized the storage screen's embedded **party** and **close box** artwork.
  The generator keeps the original palette, tile dimensions, borders, and maps.
- Localized the Pokédex cry and size-comparison captions.
- Kept every change behind `LEARNER_DEMO`; the normal Sapphire build is
  unchanged.

## Verification

- 33 automated tests pass, including width limits, generated graphics,
  compression, surrounding-pixel preservation, and required registrations.
- The learner ROM builds successfully. The Russian detailed storage screen was
  inspected in the emulator with a disposable save fixture.
- Stock Sapphire still matches SHA-1
  `3ccbbd45f8553c36463f13b938e833f652b793e4`.
- No player save files were changed. ROMs, emulator states, object files, and
  generated graphics remain ignored local files and are not committed.

## Next

Translate the remaining Pokédex species/detail content and expand the item
catalogue and item-effect messages. Then continue route-by-route NPC and battle
coverage, followed by the dialogue dictionary shortcut.
