# Play the Russian and German opening

This version translates Birch's introduction, 90 field dialogue entries,
the player-name prompt, and the clock confirmation. Room coverage includes the
GameCube, notebook, bookshelves, PC startup/email, and ordinary TV messages.
Coverage now includes Littleroot's outdoor NPCs and signs, Route 101's rescue,
the starter gift and follow-up prompts, and Mom's running shoes dialogue.
The wall map and location popups have 88 translated location labels (some
abbreviated to fit). The PC has translated menu labels, storage prompts,
mailbox prompts, and decoration controls. Its starting Potion is translated too.
The briefcase instructions and three starter labels, Pokémon nickname heading,
pause menu, save prompts and summary are translated. Route 103's rival encounter
and the Pokédex handoff now have translated field scenes with dictionary help.
Battle coverage includes 85 messages/fragments, commands, 21 early move names,
and all 18 type labels. Some menu labels are shortened to fit the original boxes.
Oldale coverage includes all 20 local dialogue entries: outdoor NPCs/sign,
both houses, shop customers, and the Pokémon Center's ground-floor visitors.
Shared nurse healing messages, shop greetings and buying prompts, Center PC
startup/primary menus, and the map heading are translated too. Oldale's five
shop items have translated names and descriptions in the buy and bag screens. Quantity
and price remain live values in the translated purchase confirmation.
It is still a partial translation: naming-keyboard button artwork, title/continue
menus, most item/decor names and descriptions, species names in
battle, later moves/effects, later TV broadcasts, and later scenes retain English.
The clock's AM/PM artwork also remains unchanged.
Shared item receipt/found/storage messages, bag action labels, basic bag prompts,
and selling confirmations now use the selected language throughout the game.
Pokédex search explanations, colors, ordering options, and search results are
translated. The shared catalogue now covers 23 common items, including stronger
potions, revives, repellents and balls. Bag pocket labels and Pokédex search-button
graphics are translated too, including during pocket-switch animations.
The upstairs link club, detailed Pokémon box interface, remaining bag prompts,
the main Pokédex/list/detail artwork and species entries, and the shop's small MONEY
graphic still need work.

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
hotkey during Birch's speech or every textbox.

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

1. Translate bag/Pokédex/naming artwork and expand the shared item catalogue,
   then finish battle-message/move coverage. Play-test the Route 103 rival fight and
   Pokédex handoff in both languages; expand route by route with a checklist.
2. Add a dictionary shortcut during dialogue that pauses and restores the current
   page. Audit button uses first; R is a candidate, not an implemented shortcut.
3. Connect exposures and dictionary requests to learner profiles, and add more
   difficulty-specific variants where they improve learning.

Full target-language immersion remains the intended final product. English
outside covered scenes is unfinished coverage, not a deliberate return to English.
