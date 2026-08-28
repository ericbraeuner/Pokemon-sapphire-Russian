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
            width = 104 if name.endswith(('Desc', 'Description')) else 184
            if width == 104 and len(demo.wrap(languages[tag], mapping, glyphs if tag == 'ru' else {}, width)) > 2:
                raise ValueError(f'Item description overflow: {name}/{tag}')
            parts.append(demo.assembly_bytes(f'LearnerUI_{tag}_{name}', demo.message(
                [languages[tag]], mapping, glyphs if tag == 'ru' else {}, font, max_width=width)))
    sources = demo.validate.load(demo.ROOT / 'language_learning/ui_sources.json')
    table = []
    for index, (symbol, entry) in enumerate(sources.items()):
        if not re.fullmatch('[A-Za-z_][A-Za-z0-9_]*', symbol):
            raise ValueError('Unsafe UI source symbol')
        labels = []
        for tag, mapping, font in [('ru', russian, 0), ('de', latin, 3)]:
            bitmap = glyphs if tag == 'ru' else {}
            if len(demo.wrap(entry[tag], mapping, bitmap, entry['width'])) > entry['lines']:
                raise ValueError(f'UI overflow: {symbol}/{tag}')
            label = f'LearnerFixed_{index}_{tag}'
            parts.append(demo.assembly_bytes(label, demo.message([entry[tag]], mapping, bitmap, font, entry['width'])))
            labels.append(label)
        table.append(f'\t.4byte {symbol}, ' + ', '.join(labels))
    import battle
    battle_parts, battle_table = battle.generate(russian, latin)
    parts.extend(battle_parts)
    table.extend(battle_table)
    import field_templates
    field_parts, field_table = field_templates.generate(russian, latin, glyphs)
    parts.extend(field_parts)
    table.extend(field_table)
    parts.append('\t.balign 4\ngLearnerUiTranslations::\n' + '\n'.join(table))
    parts.append(f'gLearnerUiTranslationCount::\n\t.2byte {len(table)}\n')
    names = demo.validate.load(demo.ROOT / 'language_learning/map_names.json')
    constants = (demo.ROOT / 'include/constants/region_map_sections.h').read_text()
    ids = re.findall(r'^\s*(MAPSEC_[A-Z0-9_]+),', constants, re.M)
    ids = ids[:ids.index('MAPSEC_NONE')]
    if set(names) != set(ids):
        raise ValueError('Map labels must cover every named region section')
    table = []
    for index, section in enumerate(ids):
        labels = []
        for tag, mapping, font in [('ru', russian, 0), ('de', latin, 3)]:
            bitmap = glyphs if tag == 'ru' else {}
            if len(demo.wrap(names[section][tag], mapping, bitmap, 96)) != 1:
                raise ValueError(f'Map popup overflow: {section}/{tag}')
            label = f'LearnerMap_{index}_{tag}'
            parts.append(demo.assembly_bytes(label, demo.message([names[section][tag]], mapping, bitmap, font, 96)))
            labels.append(label)
        table.append('\t.4byte ' + ', '.join(labels))
    parts.append('\t.balign 4\ngLearnerMapNames::\n' + '\n'.join(table))
    parts.append(f'gLearnerMapNameCount::\n\t.2byte {len(table)}\n')
    return parts
