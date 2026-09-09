# Phase 3 emulator QA checklist

Use this checklist with `pokesapphire_learner.gba` after the automated tests and
both builds pass. Test Russian and German separately. Never use the player's real
save or an old emulator save state: copy a `.sav` file to a temporary name, or
start a new disposable save.

## Acceptance rules

- Every listed label and message uses the language selected at new-game setup.
- Live values remain correct: Pokémon, move and item names, quantities, prices,
  levels, stats, money, PP and storage box numbers.
- Text stays inside its window and no glyph is raised, clipped, replaced or
  rendered as an unexpected symbol.
- Menus erase their cursors, borders and highlights when closed.
- Changing language in Settings affects the next covered interaction and survives
  an in-game save and continue.
- Guided/English-help choice affects only the initial tutorial; it never changes
  later gameplay language.

## New game and persistence

- Select Russian, each of A1 and C2, and both English-help choices.
- Repeat with German.
- Verify Birch's introduction, gender/name flow and custom-name heading.
- Set the clock and confirm that its question and Yes/No choices match the selected
  language.
- Save, close the emulator, reopen the ROM and continue. Verify language, level and
  help mode remain selected.

## Party and summary

- Open each party action, including summary, switch, item, mail and cancel.
- View summary pages for a normal Pokémon and an Egg.
- Check stats, nature, ability and description, held item, experience, move names,
  type/PP labels, encounter location, ribbons and all page headings.
- Exercise give, take and swap held-item flows, including an already-held item.
- Test move learning, replacing a move, refusing, HM refusal and the animated
  forgetting sequence.

## Bag and item effects

- Open every pocket and switch pockets in both directions.
- Exercise use, give, toss, register, deselect, check and cancel.
- Test healing HP, status and confusion; restoring PP; stat medicine; Rare Candy;
  Repel; Escape Rope; TM/HM; Coin Case; and a field-use failure.
- Obtain, find, buy, sell, deposit and withdraw items. Confirm the actual name,
  quantity and price appear in every message.

## Pokédex

- Check an unseen entry and a seen/caught entry.
- Exercise list navigation, alphabetical mode, color/type filters, sort modes,
  search results, area, cry, size comparison and return/cancel paths.
- Inspect several Hoenn species descriptions in each language for page overflow.

## Shop, storage and save/options

- Buy and sell one item and several items; test insufficient money, no bag room and
  a full shop-delivery flow. Confirm the Russian `ДЕНЬГИ` or German `GELD` sprite.
- Open Pokémon storage; exercise deposit, withdraw, move, summary, mark, name,
  release, jump, wallpaper, party, close box and cancellation/warning paths.
- Visit Options and change every setting. Verify every heading and choice, including
  text speed, battle scene/style, sound, buttons and frame.
- Save normally and test overwrite, save success and save-error text where a safe
  emulator fixture permits it.

## Battle shared flows

- Run wild, trainer, rival and double battles.
- Test send out, withdraw, switch, status, weather, stat changes, move failure,
  catching, nickname prompt, Pokédex registration, party-full PC transfer, defeat,
  victory and fleeing.
- Trigger an evolution, then test completion and cancellation.

Record each problem with language, screen, exact preceding action, screenshot and
whether it reproduces after reopening the ROM. A Phase 3 emulator pass is complete
only when every section above passes in Russian and German or has a tracked defect.
