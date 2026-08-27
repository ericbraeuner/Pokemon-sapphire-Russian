# Play the first Russian and German lesson

This is a tiny addition to Pokémon Sapphire, not a full translation. The rest
of the game stays in English. One demo ROM contains **both** languages.

## Where to find it

1. Open `pokesapphire_learner.gba` from the repository root in a GBA emulator.
2. Start a **new game**. Do not load an old emulator save state from another ROM.
3. Finish Professor Birch's introduction and leave the moving truck.
4. Follow Mom into your house. Before her normal inside-the-house dialogue,
   she offers a short language lesson.
5. Choose **Russian** or **German**. Read the greeting, then use the menu:
   **Read again**, **English hint**, **Vocabulary**, **Change language**, or
   **Continue story**. The B button also leaves the lesson.
6. Try both languages before continuing. Mom's original dialogue and clock
   instructions resume normally afterward.

The hook is shared by the boy's and girl's houses. It runs during the moving-in
scene, not every time you later talk to Mom. Use an emulator save state made in
this demo immediately before entering the house if you want to revisit it.
Keep demo saves separate from the normal game.

## What the lesson teaches

- Russian: **Привет! Добро пожаловать домой!**
- German: **Hallo! Willkommen zu Hause!**
- English: **Hello! Welcome home!**

Vocabulary help comes from each language pack. Russian `дом` means house/home;
`домой` is the directional form used in the greeting. German `zu Hause` means
at home. This first lesson uses fixed content; difficulty selection, quizzes,
pronunciation audio, and saved learning progress are not implemented yet.

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

## Limits and next steps

The Russian font supports only the glyphs needed for this lesson. The generator
fails if new content needs an unsupported glyph. German uses the existing font.
All learning state remains unchanged: using a hint currently does not record a
hint request in the external learner profile.

Next, add a short comprehension question in each language, then connect those
answers and hint requests to a learner profile before expanding the dialogue
catalogue.
