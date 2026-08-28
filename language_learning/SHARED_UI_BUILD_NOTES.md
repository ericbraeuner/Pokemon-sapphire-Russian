# Shared interface checkpoint — 2026-08-28

## Changes

- Shared item receipt, found-item and pocket messages, plus decoration storage
  messages, use Russian/German templates. Runtime item/pocket values remain live.
- Existing five shop item translations are reused by bag lists/descriptions and
  script item-name buffers. Global fixed-size item records remain unchanged.
- Bag action labels, basic prompts and return labels are translated. Selling
  quantity, confirmation and receipt messages preserve live prices/item names.
- Pokédex search descriptions, colors, ordering choices and result messages are
  translated. Copied search values receive translation before entering the large
  display buffer; search logic and alphabetical ranges are unchanged.
- The tutorial choice now asks whether to show English starting help. Removed
  its ineffective field-settings selector. Language/level remain changeable.
  Existing mode values and save layout remain compatible.
- Field template buffer validation now counts every placeholder occurrence.

## Verification

- 28 automated tests pass, including template placeholders, font restoration,
  repeated-placeholder buffer bounds and shared display hooks.
- Learner Sapphire builds successfully.
- The separate unmodified Sapphire build still matches stock SHA-1
  `3ccbbd45f8553c36463f13b938e833f652b793e4`.
- Emulator checks: German bag item/description and sale, correct 150-money credit
  and item removal; Russian Pokédex search values, descriptions and color picker;
  Russian and German shared item-gift/pocket messages using the real gift script.
- Emulator tests use separate ignored fixtures, never the player's save files.

Learner ROM: `pokesapphire_learner.gba`, 16,777,216 bytes. SHA-256:
`be40f4c607dc73ef9249f87528cbb75f8fb1f2bc763baf274207b5b975059fe3`.

## Remaining work

This is not a complete bag or Pokédex translation. Bag pocket headings, Pokédex
headings/buttons and the MONEY label are tile graphics. Species entries, most
item names/descriptions, some toss/deposit/item-effect messages, detailed box
screens and upstairs link services remain unfinished. Add shared catalogue
entries and localized artwork before expanding later areas. Dictionary access
and difficulty behavior are unchanged.
