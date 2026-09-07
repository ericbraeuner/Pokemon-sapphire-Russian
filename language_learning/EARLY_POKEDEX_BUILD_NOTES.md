# Early Pokédex entries — 2026-09-07

## Completed

- Added Russian and German Pokédex names, categories, and two description pages
  for Treecko, Torchic, Mudkip, Poochyena, Zigzagoon, and Wurmple.
- Applied the localized names to both the Pokédex list and detailed entry screen.
- Kept each description page within three short lines using a stricter width than
  the generic dialogue compiler.
- Left the original data as the fallback for every species not yet covered.

## Verification

- 34 automated tests pass.
- Russian and German Treecko list/detail screens were inspected in the emulator
  using disposable Pokédex flags. Both descriptions fit the real text panel.
- The learner ROM and stock Sapphire both build successfully. Stock Sapphire
  still matches SHA-1 `3ccbbd45f8553c36463f13b938e833f652b793e4`.
- Save structure and player save files are unchanged.

## Pokédex tab follow-up

The compact PAGE, AREA, CRY, and SIZE tabs are now localized as **Стр / Где /
Крик / Рост** and **S / Ort / Ruf / Gr**. Their upper and lower halves live in
different source-tile locations, so the generator reconstructs each button before
editing it and then writes the halves back without changing the tile map.

Later species retain their original English names and descriptions until their
entries are added to the shared selector.
