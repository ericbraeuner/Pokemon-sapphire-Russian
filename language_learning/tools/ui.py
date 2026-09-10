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
            # The Pokédex PAGE panel is narrower than an ordinary message box.
            # Keep a safety margin so proportional Cyrillic glyphs do not clip.
            width = 104 if name.endswith(('Desc', 'Description')) else 152 if 'DexPage' in name else 184
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
    items = demo.validate.load(demo.ROOT / 'language_learning/items.json')
    item_table = []
    parts.append('#include "constants/items.h"\n')
    for index, (item, languages) in enumerate(items.items()):
        if not re.fullmatch(r'ITEM_[A-Z0-9_]+', item) or set(languages) != {'ru', 'de'}:
            raise ValueError(f'Invalid item catalogue entry: {item}')
        labels = {}
        for tag, mapping, font in [('ru', russian, 0), ('de', latin, 3)]:
            entry = languages[tag]
            if set(entry) != {'name', 'description'}:
                raise ValueError(f'Invalid item language entry: {item}/{tag}')
            bitmap = glyphs if tag == 'ru' else {}
            if len(demo.wrap(entry['name'], mapping, bitmap, 88)) != 1:
                raise ValueError(f'Item name overflow: {item}/{tag}')
            if len(demo.wrap(entry['description'], mapping, bitmap, 104)) > 2:
                raise ValueError(f'Item description overflow: {item}/{tag}')
            for kind in ('name', 'description'):
                label = f'LearnerItem_{index}_{tag}_{kind}'
                labels[tag, kind] = label
                parts.append(demo.assembly_bytes(label, demo.message(
                    [entry[kind]], mapping, bitmap, font,
                    max_width=88 if kind == 'name' else 104)))
        item_table.append(
            f'\t.2byte {item}, 0\n'
            f'\t.4byte {labels["ru", "name"]}, {labels["de", "name"]}\n'
            f'\t.4byte {labels["ru", "description"]}, {labels["de", "description"]}')
    parts.append('\t.balign 4\ngLearnerItemTranslations::\n' + '\n'.join(item_table))
    parts.append(f'gLearnerItemTranslationCount::\n\t.2byte {len(item_table)}\n')
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
