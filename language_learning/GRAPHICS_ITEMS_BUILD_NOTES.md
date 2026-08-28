# Bag/search graphics and shared items — 2026-08-28

## Player-facing changes

- All five bag pocket headings now use Russian or German. The original pocket
  sliding animation and bag sprites are retained.
- Pokédex search buttons now use the selected language: search, list switching,
  exit, name, color, type, sorting, dex mode and confirmation. Short labels fit
  the original button sizes; the text underneath explains each option.
- Added 18 item translations, bringing the shared catalogue to 23. These cover
  Great/Ultra Balls, stronger potions, status cures, revives, repellents, Escape
  Rope, Rare Candy, Ether and Elixir. Shop, bag and field-item-name buffers reuse
  the same translations. Item effects, prices and save layout are unchanged.
- Descriptions now wrap to the actual 104-pixel bag/shop pane, with a maximum of
  two lines. Name checks enforce the narrower shop list width.

## Implementation and checks

`graphic_labels.json` stores wording and label coordinates. The generator reads
the original indexed PNG sheets and native font, then emits aligned 4bpp tile
arrays into ignored learner assembly. No generated images, ROMs or saves belong
in the source commit. Pillow is listed in `requirements.txt`.

- 30 automated tests pass. Graphics checks cover tile encoding, buffer sizes,
  unchanged pixels outside label interiors, and item name/description bounds.
- Learner build succeeds; Russian and German bag/search screens inspected in
  the emulator, including Russian pocket switching and a newly translated item
  received through the original gift script and displayed in the bag.
- Separate unmodified Sapphire build matches SHA-1
  `3ccbbd45f8553c36463f13b938e833f652b793e4`.
- Disposable emulator fixtures only; player saves were not opened or changed.

Learner ROM SHA-256:
`8c90530066cb0182828cde79ce8aa8cbc1c2e4b1b814a8e45e33232e4ab211b3`.

## Next work

The main Pokédex listing/detail artwork and species descriptions remain English,
as do naming-keyboard artwork and the MONEY graphic. Many later item names,
item-effect/toss/deposit messages, detailed Pokémon boxes, upstairs link services,
and later NPC scenes remain unfinished. Next, extend this graphic-label approach
to the main Pokédex and finish shared item-action messages before adding towns.
