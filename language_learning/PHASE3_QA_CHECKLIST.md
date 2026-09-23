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

## 2026-09-23 Pokédex list smoke check

Copied early-game saves opened the Pokédex list in both languages. The Russian
and German seen/caught counters, menu command, numbered list rows, and caught
Torchic entry rendered in the selected language without an overflow. This is a
list-screen check only: unseen detail pages, filters, ordering, search, area,
cry, size, and most species descriptions remain unverified. Selecting the
caught Torchic row also showed its localized category, height, weight, page
caption, and first description page in both languages without clipping. Its
other detail pages and all other species remain unverified.

Selecting Torchic's Area control exposed the stock `AREA UNKNOWN` sign for its
unavailable encounter data. The learner build now replaces that animated sign
with `НЕИЗВ.` / `UNBEK.` while retaining its original border and three-sprite
layout. The repaired sign was checked in the emulator in both languages. Area
maps with known encounter locations remain unverified.

Torchic's Cry control opened in both languages with its localized navigation
label and cry caption. Its Size control initially exposed the English dynamic
caption `SIZE COMPARED TO` because it appends the player's name after rendering.
The caption now uses the selected language (`Размер рядом с` / `Größe neben`),
and both rebuilt Size screens were checked in the emulator. Cry playback,
known-area maps, and size behavior for other species remain unverified.

The Select-button search screen was opened in both languages. Its Name, Color,
Type, Sort, View, Search, and back controls, along with the default filter
values and explanatory line, rendered without overflow. Executing a search and
checking result lists, alternative sort/filter values, and cancellation remain
unverified.

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

## 2026-09-16 targeted PC check

Using copied early-game saves and a separate ROM in `build/phase3-item-qa/`, mGBA
was driven normally from Littleroot Town through Mom's event to the player's
upstairs PC. In Russian and German, the PC opening message, main PC menu, item
storage menu, and stored Potion list rendered in the selected language. The
withdraw quantity prompt preserved the live item name and quantity of one in
both languages (`Зелье / Взять: 1.` and `Trank / Geholt: 1.`). Depositing one
Potion from the Bag likewise displayed the correct name and quantity in both
languages. The Russian deposit question was corrected from the ambiguous
`Сколько оставить?` to `Сколько положить?` and rechecked in mGBA. The captured
screens fit their windows and showed no visibly misplaced glyphs. This checks
only this one item and route; other PC branches remain unverified. These
emulator files are ignored test artifacts, not release files.

## 2026-09-16 PC quantity and cancellation follow-up

From copied Russian and German saves, depositing two Potions displayed quantity
two in the selector and the completed message (`В ПК: 2.` / `Im PC: 2.`).
Cancelling the deposit quantity prompt with B returned to the Bag with the
original stack of two still present. A second B returned to the translated PC
item-storage menu, with no lingering text box or cursor. Reopening the PC
showed a stack of two; withdrawing both rendered the selected quantity and
result message (`Взято: 2.` / `Geholt: 2.`). Cancelling the withdrawal quantity
prompt instead kept the stack of two in the PC and returned cleanly to the
translated item-storage menu. Other PC branches and storage capacity limits
remain unverified.

## 2026-09-17 Oldale mart check

Using copied early-game saves, mGBA traversed Route 101 into the Oldale mart
in both languages. A temporary Repel counter was set only in emulator RAM to
keep wild battles from interrupting the shop fixture. The clerk's greeting,
Buy/Sell/Exit menu, item list, quantity prompt, confirmation, and thank-you
message rendered in the selected language. Buying two Poke Balls showed a
total of 400 and changed the displayed money from 1050 to 650. Selling one
Potion showed a price of 150 and raised the displayed money to 800. B at each
quantity prompt returned to the preceding list, and another B returned to
the clerk menu without leaving a cursor or text box behind. In a separate
copied run, buying five Poke Balls left 50; choosing a 300-cost Potion showed
the translated insufficient-money message in both languages. The screens
fit their windows, with no visibly misplaced glyphs.

## 2026-09-17 Oldale mart quantity and capacity follow-up

Buying two Potions created a Bag stack of three. Selling two then showed a
total of 300, left one Potion in the Bag, and raised displayed money from 450
to 750 in both languages. For the no-room branch, a disposable emulator
fixture filled all 20 item-pocket slots in RAM with distinct items before a
Potion purchase. Russian showed `В сумке нет места!`; German showed `Kein Platz
im Beutel!`. The purchase was refused and the displayed money remained 1050.
No saved game or released ROM was modified by that fixture. Shop variants
outside Oldale remain unverified.

## 2026-09-17 Options and save persistence check

In both languages, the Options screen responded to changes in text speed,
battle animation, battle style, sound, button mode, and frame style. The
headings and choices fit their windows, and closing Options left no stray
border or highlight. Disposable copied saves were given Russian/C2/immersion
or German/A1/guided learner variables in emulator RAM, then saved through the
normal in-game Save menu. The save and overwrite prompts displayed in the
selected language. After closing and reopening the ROM with copies of those
new saves, the three learner values were respectively `1,6,2` and `2,1,1`,
and the changed Options choices still appeared selected. This verifies
persistence through Save/Continue; it does not by itself verify the new-game
setup selections, every frame theme, or a save-error path.

## 2026-09-17 Summary type-badge check

The learner build now substitutes Russian and German lettering in the shared
32×16 type/category icon sheet used by Pokémon Summary. Automated checks confirm
the 23-icon order and byte size, preserve each source border and the mystery
icon, and reject labels that exceed the icon interior. A rebuilt ROM was opened
in mGBA with disposable copied Russian and German saves. The Fire badge on the
Pokémon page and Normal badges on the move page rendered in the selected
language, including the full German `NORMAL` label. Summary page navigation and
return still worked. Other type/category badges have not each been exercised
in the emulator, and other Summary text remains part of the Phase 3 checklist.

## 2026-09-17 Party item handoff check

From a disposable copied German save, the Party action menu opened the translated
Item submenu (`GEBEN`, `NEHMEN`, `Zurück`). Choosing Give opened the Bag with the
correct Potion (`Trank`) and translated description. This exposed the remaining
English pocket graphic `Items`. Its shared German Bag label is now `Sachen`;
the rebuilt ROM showed `Sachen` in the same Give-item flow, and cancelling the
Bag returned cleanly to the Party action menu. Follow-up disposable runs in
both languages gave the Potion to the party Pokémon, then took it back. The
give/take messages used the live item and Pokémon names; the held-item marker
appeared after Give and cleared after Take. The action menu returned without a
stray border. The copied test Pokémon has an artificial `FFFFFFFF` nickname.
Other party/item edge cases remain unverified.

## 2026-09-17 Held-item swap and refusal check

In separate disposable Russian and German emulator runs, an Antidote was added
to the Bag in RAM alongside the saved Potion; the source saves were not edited.
After giving the Potion, selecting the Antidote showed the existing held item,
the localized Yes/No swap question, and the replacement message. Taking the
held item afterward returned Antidote (`Противоядие` / `Gegengift`), confirming
the accepted swap changed the held item. In separate runs, choosing No returned
to the Party menu without a stray border; taking the held item then returned
Potion (`Зелье` / `Trank`), confirming the refusal preserved the old item. These
runs do not cover a full Bag, a mail item, or other party edge cases.

## 2026-09-17 Bag Potion effect check

Using separate copied saves in mGBA, the Bag's Potion action menu and party
target prompt appeared in Russian and German. With the Pokémon already at full
HP, Use displayed `Это не подействует.` / `Das hat keine Wirkung.` and returned
to the Bag with the Potion quantity unchanged. In separate disposable runs,
only the Pokémon's current HP was lowered from 23 to 3 in emulator RAM. Using
the Potion restored 20 HP, showed the localized result with the live Pokémon
name, and returned to the Bag with the Potion consumed. The original saves and
released ROM were not modified by these fixtures. Other item effects remain
unverified.

## 2026-09-17 Bag Toss check

With copied Russian and German saves, Toss opened the translated quantity and
Yes/No prompts for one Potion. Choosing Yes displayed the live item name and
quantity; the completed Bag then contained only Close, confirming the Potion
was removed. The completion wording was clarified to `Выброшено: 1.` and
`Entsorgt 1.` and rechecked in the rebuilt learner ROM. Separate No runs
returned to the Bag with the Potion still present. The copied source saves
were unchanged. In additional disposable runs, a three-Potion stack was placed
in emulator RAM; selecting quantity two displayed `2` in the confirmation and
completion messages, then left exactly one Potion in the Bag in both languages.
Other pockets and capacity limits remain unverified for Toss.

## 2026-09-17 Bag pocket navigation check

Using copied saves, mGBA cycled through all five Bag pockets in both directions
in Russian and German, including wrapping from the last pocket to the first.
The shared graphic labels rendered as `Предметы`, `Покеболы`, `ТМ и НМ`,
`Ягоды`, `Важное` and `Sachen`, `Bälle`, `TM und VM`, `Beeren`, `Basis`.
The populated item and Poké Ball pockets retained their translated names and
descriptions. Empty pockets showed only the translated Close entry, and no
stray cursor or border remained after switching. This does not exercise item
actions within the empty pockets or their behavior when populated.

## 2026-09-17 Poké Ball pocket action check

In both languages, the populated Poké Ball pocket showed five balls and a
translated description. Its field Bag action menu offered Give, Toss, and
Back, without a Use action. Choosing Give opened the translated party target
prompt and displayed the live Poké Ball and Pokémon names in the result. The
disposable runs do not verify throwing a ball in battle, or other ball types.

## 2026-09-17 Escape Rope field-use failure check

An Escape Rope was added only to disposable emulator RAM in the item pocket.
Outside a cave, using it displayed the translated advice (`Совет папы: всему
своё время и место!` / `Papas Rat: Nicht jetzt, nicht hier!`). Closing the
message returned to the Bag with the Rope still at quantity one in both
languages and no leftover window. This checks a field-use failure only; using
Escape Rope successfully inside a cave remains unverified.

## 2026-09-17 Antidote and shared status-badge check

An Antidote and ordinary poison status were added only in disposable emulator
RAM. The Russian and German Party screens showed localized poison badges
(`ЯД` / `GIF`). Using the Antidote displayed the translated cure message,
cleared poison, and consumed the Antidote. The rebuilt Summary screen also
showed the localized poison badge on its pages. Automated checks preserve the
seven-badge tile layout and outer pixels; an enlarged preview was inspected to
confirm that every generated badge has visible lettering. Separate copied-save
emulator runs also displayed sleep, paralysis, burn, and freeze in both Party
and Summary, in both languages. Their labels were legible and aligned within
the original badge borders. These runs injected a status value in emulator RAM;
they do not test acquiring or curing those conditions in normal gameplay.
Faint and Pokérus remain source/preview checked only, and enemy battle
health-box badges remain unverified.

In separate copied Russian and German runs, using Antidote on the same healthy
Pokémon displayed `Это не подействует.` / `Das hat keine Wirkung.` and returned
to the Bag with the Antidote still at quantity one. The unsuccessful use did
not leave a Party window or consume the item.

Copied-save runs also added a Paralyze Heal and ordinary paralysis only in
emulator RAM. Selecting the item, choosing the party member, and closing the
result displayed the localized cure message (`Паралич снят.` / `Paralyse
geheilt.`). The paralysis badge cleared, and reopening the Bag showed the
remaining Potion but no Paralyze Heal, confirming that the successful treatment
was consumed. The same full Bag flow passed for Burn Heal, Ice Heal, and
Awakening in both languages: their results read `Ожог вылечен.` / `Brand
geheilt.`, `разморожен.` / `aufgetaut.`, and `просыпается.` / `wacht auf.`
after the live player name. In each case the status cleared and the cure item
was consumed while the original Potion remained. Full Heal likewise cleared
ordinary burn in both copied-save runs, showed `снова здоров.` / `wieder
gesund.`, and was consumed. This completes the ordinary Bag status-cure paths;
natural battle infliction and cure flows remain unverified.

## 2026-09-17 Battle health-box poison badge check

The five battle health-box status badges now use a learner-only tile range,
separate from the Party/Summary sheet. A test verifies that the original five
badges occupy exactly tile indices 0x15–0x23 in the stock health-box table and
that the generated replacements preserve their outer pixels and tile count.
From copied early-game saves, a Pokémon was poisoned only in emulator RAM and
entered a wild battle through Route 101. The player's health box showed `ЯД`
in Russian and `GIF` in German, while the HP bar and other health-box graphics
still rendered. Further copied-save runs injected sleep, paralysis, burn, and
freeze in emulator RAM and reached live wild battles in both languages. Each
player health-box badge (`СОН`, `ПАР`, `ОЖГ`, `ЛЁД` / `SCH`, `PAR`, `VER`, `EIS`)
was visibly lettered within its original border, with the HP bar intact. The
first route script sometimes stopped in tall grass without triggering combat;
the remaining cases were checked after a revised walking loop actually entered
battle. A separate wild-battle run set poison only in emulator RAM for the
opponent and showed `ЯД` in Russian and `GIF` in German in the enemy health
box. The learner hook now covers each of the four engine health-box tile ranges,
including the two used by double battles, but enemy sleep/paralysis/burn/freeze
and double-battle rendering remain unverified. These runs do not prove natural
infliction/cure flows.
