# Opening battle and menu checkpoint

## Changes

- Russian/German briefcase instructions and all three starter labels.
- Pokémon nickname heading, pause menu, save prompts and save summary.
- 85 battle templates/fragments, including encounter, send-out, command menu,
  attacks, fainting, experience, levels, common status/stat changes and escape.
- 21 early move names and 18 type labels; compact menu wording where required.
- 13 additional field scenes: Route 103 rival conversations and Pokédex handoff.
  Total: 70 field entries. New scenes share wording across difficulty levels.

## Verification

- 23 Python tests pass, including native battle token encoding, source lookup,
  unchanged short move buffers, font restoration, and dialogue integration.
- Learner Sapphire builds. Stock Sapphire SHA-1 remains
  `3ccbbd45f8553c36463f13b938e833f652b793e4`.
- Emulator: existing normal save loaded; Russian opening battle completed with
  translated commands, move/type labels, attack, fainting and experience text.
- Emulator fixtures: Russian/German nickname headings and briefcase labels.
  Fixtures re-enter the existing starter event/menu using emulated memory only;
  they do not alter the user's save or ship in the ROM.
- No save structure, nickname length, battle mechanics or progression rewards changed.

## Still unfinished

This is not a complete game translation. Remaining work includes keyboard button
artwork, battle species names, later battle messages and moves, item/bag interfaces,
and later locations. Battle dictionary access is not implemented. Route 103 and
Pokédex scripts are compiled and covered by integration checks, but their complete
playthrough still needs testing. B1 through C2 continue to share natural variants.

Normal game saves can carry forward. Back up `.sav` files and avoid loading old
emulator save states after changing the ROM. The ROM stays local and is not committed.
