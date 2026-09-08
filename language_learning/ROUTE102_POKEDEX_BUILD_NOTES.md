# Route 102 Pokédex build notes

This phase adds learner translations for the Route 102 species commonly seen
near Oldale Town: Lotad, Seedot, Ralts, and Surskit. The next early-route
batch adds Taillow, Wingull, Shroomish, and Whismur. A second early-route
batch adds Slakoth, Nincada, Skitty, and Sableye. The large follow-up batch
adds Zangoose, Seviper, Barboach, Corphish, Baltoy, Lileep, Anorith, Feebas,
Castform, Kecleon, Shuppet, Duskull, Tropius, Chimecho, Absol, Wynaut, Snorunt,
Spheal, Clamperl, and Bagon. Names, categories, and
both Pokédex description pages use the selected Russian or German language.

The shared Pokédex selector supplies these strings to the list, detail, and
cry screens, so the entries do not need separate copies in each screen. The
German noun categories are kept short enough to fit beside the game's
`POKéMON` suffix. Pokédex page generation uses a narrower safety width than
ordinary dialogue because the detail panel has less room; the 35 automated
tests cover this constraint.

## Verification

- `python -m unittest discover language_learning/tests`: 35 tests passed.
- Learner Sapphire build completed with `LEARNER_DEMO=1`.
- Headless emulator inspection confirmed Lotad #019 in Russian (`Лотад`,
  `Водный`) and German (`Loturzel`, `Wasser`), with page-one text fitting the
  detail panel in both languages.
- The disposable Pokédex fixture used for emulator inspection changes only the
  ignored test save; no user save files are part of the source change.

Next coverage target: continue the species list through the remaining early
Hoenn encounters, then expand the same shared-selector approach to evolution
entries and route NPC/battle text.
