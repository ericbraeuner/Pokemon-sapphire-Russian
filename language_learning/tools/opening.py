"""Compile translated opening scenes without changing their movement or progression."""
import re
import build_demo as demo


def load():
    data = demo.validate.load(demo.ROOT / 'language_learning/opening.json')
    ids = set()
    for entry in data['dialogues']:
        if not re.fullmatch(r'[A-Za-z]+', entry['id']) or entry['id'] in ids:
            raise ValueError('Invalid or duplicate opening ID')
        ids.add(entry['id'])
        symbol = entry['base_symbol']
        if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', symbol):
            raise ValueError('Invalid source symbol')
        floor = '2F' if '_2F_' in symbol else '1F'
        path = (demo.ROOT / entry.get('source_path', f'data/maps/LittlerootTown_BrendansHouse_{floor}/text.inc')).resolve()
        if not path.is_relative_to(demo.ROOT.resolve()) or not path.is_file():
            raise ValueError('Missing or unsafe opening source path')
        if not re.search(rf'^{re.escape(symbol)}:', path.read_text(encoding='utf-8'), re.M):
            raise ValueError(f'Missing source: {symbol}')
        for tag in ('ru', 'de'):
            if set(entry[tag]) != {'A1', 'A2', 'natural'}:
                raise ValueError('Missing authored text band')
            for lemma, gloss in entry['words'][tag]:
                if not lemma or not gloss:
                    raise ValueError('Empty dictionary entry')
    return data


def generate(russian, latin, glyphs):
    parts, scripts = [], []
    def messages(label, paragraphs, mapping, font):
        labels = []
        for paragraph in paragraphs:
            lines = demo.wrap(paragraph, mapping, glyphs if font == 0 else {})
            for offset in range(0, len(lines), 2):
                name = f'{label}_{len(labels)}'
                parts.append(demo.assembly_bytes(name, demo.message(
                    [' '.join(lines[offset:offset + 2])], mapping,
                    glyphs if font == 0 else {}, font)))
                labels.append(name)
        return ''.join(f'\tmsgbox {name}, MSGBOX_DEFAULT\n' for name in labels)

    for tag, mapping, font, labels in [
        ('Ru', russian, 0, ['Дальше', 'Ещё раз', 'Перевод', 'Словарь', 'Настройки']),
        ('De', latin, 3, ['Weiter', 'Noch einmal', 'Übersetzung', 'Wörterbuch', 'Einstellungen'])
    ]:
        for suffix, label in zip(['Next', 'Again', 'Hint', 'Words', 'Settings'], labels):
            parts.append(demo.assembly_bytes(f'LearnerMenu_{tag}{suffix}', demo.message([label], mapping, glyphs if font == 0 else {}, font)))

    for entry in load()['dialogues']:
        root = f"LearnerOpening_{entry['id']}"
        scripts.append(f'{root}::\n\tcall LearnerOpening_EnsureSettings\n'
                       f'\tcompare VAR_LEARNER_LANGUAGE, 1\n\tgoto_if_eq {root}_ru\n\tgoto {root}_de\n')
        for tag, mapping, font in [('ru', russian, 0), ('de', latin, 3)]:
            base = f'{root}_{tag}'
            scripts.append(f'{base}:\n\tcompare VAR_LEARNER_LEVEL, 1\n\tgoto_if_eq {base}_A1\n'
                           f'\tcompare VAR_LEARNER_LEVEL, 2\n\tgoto_if_eq {base}_A2\n\tgoto {base}_natural\n')
            for band in ('A1', 'A2', 'natural'):
                label = f'{base}_{band}'
                scripts.append(f'{label}:\n' + messages(label + 'Text', entry[tag][band], mapping, font) + f'\tgoto {base}_Menu\n')
            scripts.append(f'{base}_Menu:\n\tclosemessage\n\tmultichoice 0, 0, MULTI_LEARNER_{tag.upper()}, 0\n'
                           f'\tcompare VAR_RESULT, 1\n\tgoto_if_eq {base}\n'
                           f'\tcompare VAR_RESULT, 2\n\tgoto_if_eq {base}_Hint\n'
                           f'\tcompare VAR_RESULT, 3\n\tgoto_if_eq {base}_Words\n'
                           f'\tcompare VAR_RESULT, 4\n\tgoto_if_eq {base}_Settings\n\treturn\n')
            scripts.append(f'{base}_Hint:\n' + messages(base + 'HintText', entry['english'], latin, 3) + f'\tgoto {base}_Menu\n')
            scripts.append(f'{base}_Words:\n' + messages(base + 'WordsText', [f'{lemma}: {gloss}' for lemma, gloss in entry['words'][tag]], mapping, font) + f'\tgoto {base}_Menu\n')
            scripts.append(f'{base}_Settings:\n\tcall LearnerOpening_Settings\n\tgoto {root}\n')
    return parts + scripts
