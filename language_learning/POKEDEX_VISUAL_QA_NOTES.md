# Pokédex visual QA

Phase 2 checked representative entries at the beginning, middle, and end of
the 202-entry regional Pokédex in both learner languages. Earlier checks cover
Treecko and Lotad; this pass inspected Wailord (#100), Jigglypuff (#138), and
Deoxys (#202), including long names, categories, and wrapped descriptions.

The review found that the stock category copier counted invisible learner font
control bytes against its eleven-byte limit. This truncated otherwise valid
categories, such as German `Flutwal`. The learner build now permits up to 23
encoded bytes while retaining room in the 32-byte destination for the appended
`POKéMON` label. Stock builds retain the original eleven-byte behavior.

Automated coverage now verifies all 202 regional entries, a ten-byte species
name limit, a sixteen-byte visible category limit, category pixel width, and a
three-line description limit. Emulator inspection confirmed the fixed German
`Flutwal POKéMON`, Russian `Плавучий кит POKéMON`, German Jigglypuff, and both
Russian and German Deoxys screens without clipping.
