# Pokédex controls and item actions — 2026-08-28

## Completed

- Localized the list menu's return, top, bottom and close controls, plus the
  seen/caught and menu/search sprite captions. Russian counter labels are neutral
  rather than depending on the player's gender. Original START/SELECT button
  names are retained as physical controller labels.
- Extended the deterministic tile generator to the main background and sprite
  sheets. Sprite data uses a native literal LZ77 stream and the original size/tag.
  Detail, cry and size pages reload the same localized background sheet.
- Localized discard confirmation/result and PC deposit-result messages. Their
  item names and quantities are expanded into the existing large display buffer,
  with separate 104-pixel validation for the small bag pane.
- Added shared item-use, Repel, flute, detector, bike and common error messages.
  Item-use code uses the shared translated names without changing item effects.
- Shortened bag action labels to fit the two-column layout after emulator testing
  exposed an overlap in the previous German discard button.

## Verification

- 32 automated tests pass, including sprite compression round-trip, unchanged
  surrounding tile pixels, template fields, font restoration and narrow panes.
- Learner build succeeds. Russian and German Pokédex menus inspected in the
  emulator; final Russian neutral counter labels fit.
- German discard cancellation kept the Potion. Confirmation displayed the
  translated result and removed exactly that one item. Russian Repel use displayed
  the translated player/item message. These tests used disposable fixtures only.
- Stock Sapphire still matches SHA-1
  `3ccbbd45f8553c36463f13b938e833f652b793e4`.
- Save layout and player save files are unchanged. Only source and documentation
  are committed; generated graphics, test states and ROMs remain local/ignored.

Current ROM SHA-256:
`8f76277ce33c6968135da332f53b84ac14dd6a4d55885b8023b6e6e149c9c6a0`.

The prior unreviewed ROM is preserved locally at
`build/releases/pokesapphire_learner_0be317267.gba`, SHA-256
`8c90530066cb0182828cde79ce8aa8cbc1c2e4b1b814a8e45e33232e4ab211b3`.
Use normal in-game saves across builds, not old emulator save states.

## Next

Continue detailed Pokémon storage menus, remaining Pokédex detail artwork and
species entries, and wider item-effect messages. The game is still partially
translated; the upstairs link services, later battles and later NPC scenes also
need coverage. No new difficulty system or dictionary hotkey was added here.
