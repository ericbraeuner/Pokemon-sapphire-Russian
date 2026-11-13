"""Compile translated opening scenes without changing their movement or progression."""
import re
import build_demo as demo


def _template_width(text, mapping, glyphs, widths):
    total = 0
    for part in re.split(r'(\{[^}]+\})', text):
        if part.startswith('{'):
            total += widths[part[1:-1]]
        else:
            total += sum(len(glyphs[c][0]) + 1 if c in glyphs else 8 for c in part)
    return total


def _wrap_template(text, mapping, glyphs, widths, max_width=192):
    lines = []
    current = ''
    for word in text.split():
        if _template_width(word, mapping, glyphs, widths) > max_width:
            raise ValueError(f'Template word exceeds message width: {word}')
        candidate = f'{current} {word}' if current else word
        if current and _template_width(candidate, mapping, glyphs, widths) > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    result = lines[0]
    for index, line in enumerate(lines[1:], 1):
        result += (r'\n' if index % 2 else r'\p') + line
    return result


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
        if entry.get('adaptive_translation') not in (None, True):
            raise ValueError('adaptive_translation must be true when present')
    return data


def generate(russian, latin, glyphs):
    import field_templates
    field_entries = demo.validate.load(demo.ROOT / 'language_learning/field_templates.json')
    parts, scripts, shortcut_handlers, adaptive_table = [], [], [], []
    def messages(label, paragraphs, mapping, font, dictionary=None, count_exposure=False,
                 template_entry=None):
        labels = []
        for paragraph in paragraphs:
            if '{' in paragraph:
                if template_entry is None:
                    raise ValueError('Runtime text token has no field-template metadata')
                bitmap = glyphs if font == 0 else {}
                widths = template_entry.get('widths', {})
                wrapped = _wrap_template(paragraph, mapping, bitmap, widths,
                                         template_entry.get('max_width', 192))
                name = f'{label}_{len(labels)}'
                parts.append(demo.assembly_bytes(name, field_templates.compile_text(
                    wrapped, mapping, bitmap, font, widths,
                    template_entry.get('max_width', 192),
                    template_entry.get('buffer_lengths'))))
                labels.append(name)
                continue
            lines = demo.wrap(paragraph, mapping, glyphs if font == 0 else {})
            for offset in range(0, len(lines), 2):
                name = f'{label}_{len(labels)}'
                parts.append(demo.assembly_bytes(name, demo.message(
                    [' '.join(lines[offset:offset + 2])], mapping,
                    glyphs if font == 0 else {}, font)))
                labels.append(name)
        commands = []
        for name in labels:
            if count_exposure:
                commands.append('\tcall LearnerOpening_RecordExposure\n')
            if dictionary is None:
                commands.append(f'\tmsgbox {name}, MSGBOX_DEFAULT\n')
                continue
            display = f'{name}_Display'
            handler = f'{name}_Dictionary'
            commands.append(f'{display}:\n\tmsgbox {name}, MSGBOX_DEFAULT\n'
                            f'\tcompare VAR_LEARNER_DICTIONARY_REQUEST, 1\n'
                            f'\tgoto_if_eq {handler}\n')
            shortcut_handlers.append(f'{handler}:\n\tsetvar VAR_LEARNER_DICTIONARY_REQUEST, 0\n'
                                     f'\tcall LearnerOpening_RecordDictionaryRequest\n'
                                     f'\tcall {dictionary}\n\tgoto {display}\n')
        return ''.join(commands)

    for tag, mapping, font, labels in [
        ('Ru', russian, 0, ['Дальше', 'Ещё раз', 'Перевод', 'Словарь', 'Настройки']),
        ('De', latin, 3, ['Weiter', 'Noch einmal', 'Übersetzung', 'Wörterbuch', 'Einstellungen'])
    ]:
        for suffix, label in zip(['Next', 'Again', 'Hint', 'Words', 'Settings'], labels):
            parts.append(demo.assembly_bytes(f'LearnerMenu_{tag}{suffix}', demo.message([label], mapping, glyphs if font == 0 else {}, font)))

    dialogues = load()['dialogues']
    dictionary_dispatch = [
        'LearnerOpening_RecordExposure::\n'
        '\tcopyvar VAR_LEARNER_LAST_EXPOSURE_CONTEXT, VAR_LEARNER_DICTIONARY_CONTEXT\n'
        '\tcompare VAR_LEARNER_EXPOSURE_COUNT, 0xFFFF\n'
        '\tgoto_if_eq LearnerOpening_RecordExposure_Return\n'
        '\taddvar VAR_LEARNER_EXPOSURE_COUNT, 1\n'
        'LearnerOpening_RecordExposure_Return:\n\treturn\n',
        'LearnerOpening_RecordDictionaryRequest::\n'
        '\tcopyvar VAR_LEARNER_LAST_DICTIONARY_CONTEXT, VAR_LEARNER_DICTIONARY_CONTEXT\n'
        '\tcompare VAR_LEARNER_DICTIONARY_COUNT, 0xFFFF\n'
        '\tgoto_if_eq LearnerOpening_RecordDictionaryRequest_Return\n'
        '\taddvar VAR_LEARNER_DICTIONARY_COUNT, 1\n'
        'LearnerOpening_RecordDictionaryRequest_Return:\n\treturn\n',
        'LearnerOpening_OpenCurrentDictionary::'
    ]
    for context_id, entry in enumerate(dialogues, 1):
        root = f"LearnerOpening_{entry['id']}"
        scripts.append(f'{root}::\n\tcall LearnerOpening_EnsureSettings\n'
                       f'\tsetvar VAR_LEARNER_DICTIONARY_CONTEXT, {context_id}\n'
                       f'\tsetvar VAR_LEARNER_DICTIONARY_REQUEST, 0\n'
                       f'\tsetvar VAR_LEARNER_ADAPTIVE_VARIANT, 0\n\tdelay 1\n'
                       f'\tcompare VAR_LEARNER_LANGUAGE, 1\n\tgoto_if_eq {root}_ru\n\tgoto {root}_de\n')
        dictionary_dispatch.append(
            f'\tcompare VAR_LEARNER_DICTIONARY_CONTEXT, {context_id}\n'
            f'\tgoto_if_eq {root}_Dictionary\n')
        for tag, mapping, font in [('ru', russian, 0), ('de', latin, 3)]:
            base = f'{root}_{tag}'
            scripts.append(f'{base}:\n\tcompare VAR_LEARNER_ADAPTIVE_VARIANT, 1\n\tgoto_if_eq {base}_A1\n'
                           f'\tcompare VAR_LEARNER_ADAPTIVE_VARIANT, 2\n\tgoto_if_eq {base}_A2\n'
                           f'\tcompare VAR_LEARNER_ADAPTIVE_VARIANT, 3\n\tgoto_if_eq {base}_natural\n'
                           f'\tcompare VAR_LEARNER_LEVEL, 1\n\tgoto_if_eq {base}_A1\n'
                           f'\tcompare VAR_LEARNER_LEVEL, 2\n\tgoto_if_eq {base}_A2\n\tgoto {base}_natural\n')
            for band in ('A1', 'A2', 'natural'):
                label = f'{base}_{band}'
                scripts.append(f'{label}:\n' + messages(label + 'Text', entry[tag][band], mapping, font,
                                                        f'{base}_WordsDisplay', True,
                                                        field_entries.get(entry['base_symbol']))
                               + f'\tgoto {base}_Menu\n')
            scripts.append(f'{base}_Menu:\n\tclosemessage\n\tmultichoice 0, 0, MULTI_LEARNER_{tag.upper()}, 0\n'
                           f'\tcompare VAR_RESULT, 1\n\tgoto_if_eq {base}\n'
                           f'\tcompare VAR_RESULT, 2\n\tgoto_if_eq {base}_Hint\n'
                           f'\tcompare VAR_RESULT, 3\n\tgoto_if_eq {base}_Words\n'
                           f'\tcompare VAR_RESULT, 4\n\tgoto_if_eq {base}_Settings\n'
                           f'\tsetvar VAR_LEARNER_DICTIONARY_CONTEXT, 0\n'
                           f'\tsetvar VAR_LEARNER_DICTIONARY_REQUEST, 0\n\treturn\n')
            scripts.append(f'{base}_Hint:\n' + messages(base + 'HintText', entry['english'], latin, 3,
                                                         f'{base}_WordsDisplay') + f'\tgoto {base}_Menu\n')
            scripts.append(f'{base}_Words:\n\tcall LearnerOpening_RecordDictionaryRequest\n'
                           f'\tcall {base}_WordsDisplay\n\tgoto {base}_Menu\n')
            scripts.append(f'{base}_WordsDisplay:\n\tsetvar VAR_LEARNER_DICTIONARY_REQUEST, 0\n'
                           + messages(base + 'WordsText', [f'{lemma}: {gloss}' for lemma, gloss in entry['words'][tag]], mapping, font)
                           + '\tsetvar VAR_LEARNER_DICTIONARY_REQUEST, 0\n\treturn\n')
            scripts.append(f'{base}_Settings:\n\tcall LearnerOpening_Settings\n\tgoto {root}\n')
        if entry.get('adaptive_translation'):
            labels = []
            for tag in ('ru', 'de'):
                for band in ('A1', 'A2', 'natural'):
                    if len(entry[tag][band]) != 1:
                        raise ValueError(f'Adaptive translation must be one paragraph: {entry["id"]}/{tag}/{band}')
                    label = f'{root}_{tag}_{band}AdaptiveText'
                    mapping = russian if tag == 'ru' else latin
                    font = 0 if tag == 'ru' else 3
                    text = entry[tag][band][0]
                    bitmap = glyphs if tag == 'ru' else {}
                    if '{' in text:
                        field_entry = field_entries[entry['base_symbol']]
                        widths = field_entry.get('widths', {})
                        wrapped = _wrap_template(text, mapping, bitmap, widths,
                                                 field_entry.get('max_width', 192))
                        data = field_templates.compile_text(
                            wrapped, mapping, bitmap, font, widths,
                            field_entry.get('max_width', 192),
                            field_entry.get('buffer_lengths'))
                    else:
                        data = demo.message(entry[tag][band], mapping, bitmap, font)
                    parts.append(demo.assembly_bytes(label, data))
                    labels.append(label)
            adaptive_table.append(f'\t.4byte {entry["base_symbol"]}, ' + ', '.join(labels)
                                  + f'\n\t.2byte {context_id}, 0')
        scripts.append(f'{root}_Dictionary:\n\tcompare VAR_LEARNER_LANGUAGE, 1\n'
                       f'\tgoto_if_eq {root}_ru_WordsDisplay\n\tgoto {root}_de_WordsDisplay\n')
    dictionary_dispatch.append('\treturn\n')
    parts.append('\t.balign 4\ngLearnerAdaptiveTranslations::\n'
                 + ('\n'.join(adaptive_table) if adaptive_table else '\t.4byte 0') + '\n')
    parts.append(f'gLearnerAdaptiveTranslationCount::\n\t.2byte {len(adaptive_table)}\n')
    return parts + dictionary_dispatch + scripts + shortcut_handlers
