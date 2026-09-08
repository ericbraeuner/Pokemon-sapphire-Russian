# Pokédex visual QA

Phase 2 captured and reviewed every page of the 202-entry regional Pokédex in
both learner languages: 202 Pokémon x 2 description pages x 2 languages, or
808 emulator screenshots. The capture set was checked for unique sequential
entries before its 44 contact sheets were inspected for clipped text, misplaced
glyphs, bad wrapping, missing content, and visible encoding errors.

The review found that the stock category copier counted invisible learner font
control bytes against its eleven-byte limit. This truncated otherwise valid
categories, such as German `Flutwal`. The learner build now permits up to 23
encoded bytes while retaining room in the 32-byte destination for the appended
`POKéMON` label. Stock builds retain the original eleven-byte behavior.

Automated coverage verifies all 202 regional entries, all 404 distinct
descriptions per language, terminal punctuation and clean whitespace, a
ten-byte species-name limit, a sixteen-byte visible category limit, category
pixel width, and a three-line description limit. The exhaustive emulator review
confirmed that every Russian and German name, category, and description fits.
It also prompted two German grammar corrections (`heißes Magma` and `als das
schönste Pokémon`).
