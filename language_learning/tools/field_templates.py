"""Bounded field UI templates that retain runtime quantities and prices."""
import re
import build_demo as demo

TOKENS = {'PLAYER': 1, 'STR_VAR_1': 2, 'STR_VAR_2': 3, 'STR_VAR_3': 4}

def compile_text(text, mapping, glyphs, font, widths, max_width=192):
    data = [0xFC, 22, 0xFC, 6, font]
    width = 0
    expanded_budget = 0
    for part in re.split(r'(\{[^}]+\}|\\[npl])', text):
        if part in (r'\n', r'\p'):
            width = 0
            data.extend([0xFE] if part == r'\n' else [0xFC, 6, 3, 0xFB, 0xFC, 6, font])
        elif part == '{PAUSE_UNTIL_PRESS}':
            data.extend([0xFC, 9])
        elif part.startswith('{'):
            token = part[1:-1]
            data.extend([0xFD, TOKENS[token]])
            data.extend([0xFC, 6, font])
            width += widths[token]
            expanded_budget += widths[token]
        else:
            data.extend(demo.encode(part, mapping))
            width += sum(len(glyphs[c][0]) + 1 if c in glyphs else 8 for c in part)
        if width > max_width:
            raise ValueError('Expanded field template exceeds text box')
    data.extend([0xFC, 7, 0xFF])
    if len(data) + expanded_budget > 240:
        raise ValueError('Expanded field template exceeds buffer budget')
    return data

def generate(russian, latin, glyphs):
    entries = demo.validate.load(demo.ROOT / 'language_learning/field_templates.json')
    parts, table = [], []
    for i, (symbol, entry) in enumerate(entries.items()):
        if not re.fullmatch(r'[A-Za-z_]\w*', symbol):
            raise ValueError('Invalid field template symbol')
        labels = []
        for tag, mapping, font in [('ru', russian, 0), ('de', latin, 3)]:
            label = f'LearnerFieldTemplate_{i}_{tag}'
            try:
                data = compile_text(entry[tag], mapping, glyphs if tag == 'ru' else {}, font, entry.get('widths', {}), entry.get('max_width', 192))
            except (ValueError, KeyError) as exc:
                raise ValueError(f'{symbol}/{tag}: {exc}') from exc
            parts.append(demo.assembly_bytes(label, data))
            labels.append(label)
        table.append('\t.4byte ' + ', '.join([symbol] + labels))
    return parts, table
