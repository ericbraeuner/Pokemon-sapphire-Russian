"""Compile curated vocabulary for ordinary translated field messages."""
import re
import build_demo as demo


def load():
    entries = demo.validate.load(demo.ROOT / 'language_learning/field_dictionary.json')
    translated = demo.validate.load(demo.ROOT / 'language_learning/field_templates.json')
    translated.update(demo.validate.load(demo.ROOT / 'language_learning/ui_sources.json'))
    for symbol, languages in entries.items():
        if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', symbol):
            raise ValueError(f'Unsafe field dictionary symbol: {symbol}')
        if symbol not in translated or set(languages) != {'ru', 'de'}:
            raise ValueError(f'Unknown or incomplete field dictionary entry: {symbol}')
        for tag, words in languages.items():
            if not words or any(not isinstance(word, list) or len(word) != 2
                                or not all(isinstance(value, str) and value.strip() for value in word)
                                for word in words):
                raise ValueError(f'Invalid field dictionary words: {symbol}/{tag}')
            if tag == 'de':
                for lemma, _ in words:
                    if lemma[0].isupper() and not re.match(r'^(der|die|das) ', lemma):
                        raise ValueError(f'German noun lacks article: {symbol}/{lemma}')
    return entries


def generate(russian, latin, glyphs):
    parts, table = [], []
    for index, (symbol, languages) in enumerate(load().items()):
        labels = []
        for tag, mapping, font in [('ru', russian, 0), ('de', latin, 3)]:
            label = f'LearnerFieldDictionary_{index}_{tag}'
            pages = [f'{lemma}: {gloss}' for lemma, gloss in languages[tag]]
            parts.append(demo.assembly_bytes(label, demo.message(
                pages, mapping, glyphs if tag == 'ru' else {}, font)))
            labels.append(label)
        table.append(f'\t.4byte {symbol}, {labels[0]}, {labels[1]}')
    parts.append('\t.balign 4\ngLearnerFieldDictionaries::\n' + '\n'.join(table))
    parts.append(f'gLearnerFieldDictionaryCount::\n\t.2byte {len(table)}\n')
    return parts
