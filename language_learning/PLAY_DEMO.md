# Play the Russian and German opening

This version translates Birch's introduction, the player-name prompt, and the
clock confirmation. Its automated source audit now covers every exported text
label used by active Pokémon Sapphire maps, plus shared services and special
events that live outside individual map files. Room coverage includes the
GameCube, notebook, bookshelves, PC startup/email, and ordinary TV messages.
Coverage now includes Littleroot's outdoor NPCs and signs, Route 101's rescue,
the starter gift and follow-up prompts, and Mom's running shoes dialogue.
The wall map and location popups have 88 translated location labels (some
abbreviated to fit). The PC has translated menu labels, storage prompts,
mailbox prompts, and decoration controls. Its starting Potion is translated too.
The briefcase instructions and three starter labels, Pokémon nickname heading,
pause menu, save prompts and summary are translated. Route 103's rival encounter
and the Pokédex handoff now have translated field scenes with dictionary help.
Battle coverage includes all 456 user-visible message templates, all 354 gameplay
move names, battle commands, and all 18 type labels. The 23 omitted engine strings
are empty, punctuation, formatting, or internal composition fragments. Some move
and menu labels are shortened to fit the original boxes.
Oldale coverage includes all 20 local dialogue entries: outdoor NPCs/sign,
both houses, shop customers, and the Pokémon Center's ground-floor visitors.
Shared nurse healing messages, shop greetings and buying prompts, Center PC
startup/primary menus, and the map heading are translated too. Oldale's five
shop items have translated names and descriptions in the buy and bag screens. Quantity
and price remain live values in the translated purchase confirmation.
All 202 regional Pokédex entries, all 339 named usable items, all 354 gameplay
moves, 77 abilities, battle species names, and active field scenes have bilingual
runtime paths. Some tile-based artwork still needs a visual audit, including the
naming keyboard and clock's AM/PM graphic. Debug, unused, and Ruby-exclusive text
is intentionally outside the Sapphire translation catalogue.
Shared item receipt/found/storage messages, bag action labels, basic bag prompts,
and selling confirmations now use the selected language throughout the game.
Pokédex search explanations, colors, ordering options, and search results are
translated. The shared catalogue now covers all 339 named, usable items, including
medicines, balls, held items, berries, key items, mail, and all 58 TMs/HMs.
Each machine description names the move it teaches. Bag pocket labels and Pokédex search-button
graphics are translated too, including during pocket-switch animations.
Pokédex list navigation, seen/caught counters and menu/search captions now use
the selected language. Bag discard confirmations/results and PC item-deposit
results keep their actual item name and quantity. Field item-use messages and
several common item errors are translated. Compact action buttons fit the bag's
two-column menu without overlapping.
The upstairs link club, detailed Pokémon storage, shared Bag prompts, Pokédex
interface artwork, and the shop's MONEY graphic are bilingual. Source coverage is
broader than emulator coverage, so uncommon branches still need live playtesting
for layout, menu cleanup, and contextual wording.

## Try it

1. Open `pokesapphire_learner.gba`. Start a **new game** to see the new setup.
   Do not load an emulator save state from an older ROM build.
2. Before Birch speaks, the **Language** screen lets you choose Russian or German.
3. Choose A1–C2, then whether to show English starting help. B returns to the previous
   setup screen. The first language screen requires a choice.
4. Yes adds a short English controls explanation; No skips it. Birch speaks the
   chosen language either way. This only affects the start of a new game, not
   dictionary access or the language of later dialogue.
5. Follow Mom from the truck into the house, set the clock, and watch the TV
   sequence. The language and level carry across these scenes without reselecting.
   The clock confirmation uses the chosen language, including Yes/No.
   Try the PC and wall map upstairs, then the town signs, NPCs, neighbor and lab.
6. Help menus provide Next, Read again, Translation, Dictionary, and Settings in
   the selected language. B means Next; story actions still run normally.
   During one of the 90 authored learning dialogues, or one of the first 60
   curated common field messages, wait for the current text page to finish and
   press **R** to open its dictionary immediately. Closing the dictionary replays
   that page so you do not lose your place.
7. Change language or level in a translated scene's Settings menu. A new
   choice applies to subsequent covered interactions, including the clock.
   The new-game tutorial choice is no longer offered here because it has no
   effect after the introduction.
8. Use the normal game SAVE to store your choices with your progress.
   Continue loads them without opening new-game setup. Old learner saves with
   a language/level but no mode default to guided mode without losing their choices.

Keep experimental saves separate from the unmodified game. Normal `.sav` saves
and emulator save states are different; the latter contain ROM-specific pointers.

## Language and difficulty

German nouns include articles, such as **das Haus**, **die Uhr**, and
**der Schreibtisch**. Fixed phrases such as **zu Hause** stay intact. Russian
has no articles. Definition separators use a semicolon and space, as in `home; house`. The Russian font now
aligns capitals with the lowercase baseline; accents and descenders are intentional.

- A1: shorter sentences in scenes with authored difficulty variants.
- A2: more connected sentences.
- B1–C2: shared natural dialogue, with dictionary help still available.

The introductory speech and short TV lines currently use common wording across
levels. These are learning targets, not certified CEFR assessments or six distinct
translations of every sentence. There is no adaptive progression or vocabulary
tracking yet. Help is available after translated field scenes; it is not yet a
hotkey during every translated textbox or in battle.

## Building it

From the repository root in a configured build shell:

```sh
make -f language_learning/Makefile test
make -j8 GAME_VERSION=SAPPHIRE LEARNER_DEMO=1
```

Python 3.10 or later, Pillow, agbcc, the host tools, and devkitARM are required.
Install the Python dependency with `python -m pip install -r language_learning/requirements.txt`.
Pillow reads the existing indexed graphics and bitmap font; only source code and
label text are committed, while generated tile arrays stay in the ignored build.
On this
Windows setup, use MSYS2 with `/mingw64/bin` and devkitARM on `PATH`. If `python3`
is unavailable, pass `PYTHON=/path/to/python.exe` to both commands. For example:

```sh
export PATH=/mingw64/bin:/opt/devkitpro/devkitARM/bin:/usr/bin:$PATH
export DEVKITARM=/opt/devkitpro/devkitARM
make -f language_learning/Makefile test PYTHON=/c/Users/ericb/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe
make -j8 GAME_VERSION=SAPPHIRE LEARNER_DEMO=1 PYTHON=/c/Users/ericb/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe
```

The normal game is still built separately with `make sapphire COMPARE=1`.
Do not expect the demo ROM to match the original game's hash.

## Next development milestones

1. Run the remaining emulator checklist in both languages, especially uncommon
   services, minigames, Secret Bases, event-ticket scenes, and late-game branches.
   Source and width checks cannot prove that every window closes and redraws well.
2. Expand the R-button dictionary shortcut beyond the 90 authored learning
   dialogues and first 60 shared field messages as more curated vocabulary is added.
3. Connect exposures and dictionary requests to learner profiles, add more
   difficulty-specific variants where they improve learning, and obtain a
   native-speaker editorial review of Russian and German wording.

Full target-language immersion remains the intended final product. Any English
found in an active Sapphire scene should be reported as a missed runtime path or
graphic rather than treated as deliberate behavior.
