# Oldale translation checkpoint

## Added

- 20 local dialogue entries covering Oldale's outdoor NPCs, town sign, two houses,
  shop visitors and Pokémon Center ground-floor visitors. Each has dictionary help.
- Shared nurse messages, healing prompts, shop greeting/farewell, buying menu and
  quantity/price confirmation. Native choices and transaction logic are unchanged.
- Shared Center PC startup, computer selection and Pokémon storage primary menu.
  The PC menu now measures translated labels rather than assuming an 8-tile width.
- Translated Hoenn map heading and shared shop/Center signs.
- Five Oldale shop item names/descriptions, scoped to the buying interface.

## Checks

- 26 Python tests: all Oldale local text symbols covered, lesson hooks retain base
  text, shop placeholders retain quantities/prices, and item buffers stay unchanged.
- Emulator checks use a disposable copy of the earlier normal save and map-entry
  fixtures. Russian healing, PC menus, map, shop and purchase were exercised.
  Buying two antidotes displayed a total of 200 and reduced money from 3000 to 2800.
  German house dialogue, PC menu and shop item descriptions were inspected.
- Final learner build succeeds. The separate stock build still matches SHA-1
  `3ccbbd45f8553c36463f13b938e833f652b793e4`. German purchase confirmation was
  checked again after reverting the money-label experiment.
- Saves, prices, inventory structures and healing scripts were not changed.
- ROM and emulator fixtures remain local, outside the source commit.

## Remaining coverage

Upstairs link-club services, detailed box screens, selling/bag interfaces and the
small MONEY artwork still contain English. The attempted tile-based money heading
was removed after a transient overlap with the confirmation menu was observed.
Other towns and later battle content remain unfinished. Oldale's current A1/A2/
natural entries share wording; differentiated CEFR variants are a later pass.
