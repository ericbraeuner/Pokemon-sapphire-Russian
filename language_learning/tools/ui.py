"""Compile bounded strings for C interfaces as well as script dialogue."""
import re
import build_demo as demo

def generate(russian, latin, glyphs):
    entries = demo.validate.load(demo.ROOT / 'language_learning/ui.json')
    parts = []
    for name, languages in entries.items():
        if not re.fullmatch('[A-Za-z]+', name) or set(languages) != {'ru', 'de'}:
            raise ValueError('Invalid UI key or missing translation')
        for tag, mapping, font in [('ru', russian, 0), ('de', latin, 3)]:
            parts.append(demo.assembly_bytes(f'LearnerUI_{tag}_{name}', demo.message(
                [languages[tag]], mapping, glyphs if tag == 'ru' else {}, font, max_width=184)))
    return parts
