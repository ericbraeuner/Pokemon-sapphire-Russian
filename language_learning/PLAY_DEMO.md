# Play the Russian and German opening

This build translates six house dialogue scenes in both languages. It is not
yet a fully translated game. The introduction, later scenes, clock interface,
battles, and general menus still contain English.

## Try it

1. Open `pokesapphire_learner.gba` in a GBA emulator. Start a **new game**; do not
   load a save state from an older ROM build. Keep demo saves separate.
2. Finish Birch's introduction, leave the truck, and follow Mom inside.
3. Choose Russian or German, then A1, A2, B1, B2, C1, or C2.
4. Continue through Mom's welcome, moving/room instructions, and upstairs clock
   scene. The translated dialogue replaces the English lines in those scenes.
5. After each scene, choose Next, Read again, Translation, Dictionary, or Settings.
   These labels appear in your selected language. B means Next in the help menu;
   it does not skip movement or story requirements. Settings cannot be cancelled
   before a valid language and level are selected.
6. Use the game's normal SAVE when available to save language and level together
   with game progress. They are remembered between maps without saving too.

German nouns include their articles: **das Haus**, **das Zimmer**, **die Uhr**,
**der Umzug**, **die Zeit**, **der Schreibtisch**. Fixed phrases such as
**zu Hause** stay intact. Russian has no articles. Russian **часы** is a plural
noun meaning clock or watch. Definition separators display as commas to avoid
the base font's misleading semicolon glyph.

## Difficulty in this build

- A1: short, direct sentences.
- A2: more connected sentences.
- B1–C2: the same natural dialogue, with dictionary help still available.

These are authored learning targets, not certified CEFR assessments. There are
three text versions per scene, not six distinct translations. C2 does not mean
every sentence needs advanced vocabulary. English translations appear only
when requested within these covered scenes; settings instructions still use
English. There is no adaptive difficulty or vocabulary tracking yet.

## Building it

From the repository root in a configured build shell:

```sh
make -f language_learning/Makefile test
make -j8 GAME_VERSION=SAPPHIRE LEARNER_DEMO=1
```

Python 3.10 or later, agbcc, the host tools, and devkitARM are required. On this
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

## Development direction

The intended product keeps the selected target language throughout the game.
The remaining English is unfinished coverage, not the intended learning loop.

Next milestones:

1. Move language, level, and guided/immersion mode selection before Birch's
   introduction. Guided mode can explain controls in English; immersion mode
   should use the chosen language immediately. This is not implemented yet.
2. Translate the whole Littleroot opening, then expand route by route while
   preserving story instructions. Translate game interfaces as well as dialogue.
3. Add an in-dialogue dictionary shortcut (candidate: R) that pauses and restores
   the exact text position. Audit existing button uses before assigning it.
4. Add more level-specific text where useful and connect dictionary requests to
   learner profiles. Keep dictionary access in every mode, including C2.

The current help menu is a temporary interface, not the final dictionary hotkey.
The boy and girl share the same translated house hooks. Other dialogue and
interfaces must still be translated before claiming full immersion.
