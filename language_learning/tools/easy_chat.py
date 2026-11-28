"""Compile Trainer Card vocabulary in the existing Easy Chat word order."""
import re

import build_demo as demo


GROUPS = (
    'pokemon', 'trainer', 'status', 'battle', 'greetings', 'people',
    'voices', 'speech', 'endings', 'feelings', 'conditions', 'actions',
    'lifestyle', 'hobbies', 'time', 'misc', 'adjectives', 'events',
    'move_1', 'move_2', 'trendy_saying', 'pokemon_2',
)

# The stock keyboard has 26 letter positions and one position for symbols.
ALPHABET_KEYS = {
    'ru': 'А Б В Г Д ЕЁ Ж З ИЙ К Л М Н О П Р С Т У ФХ ЦЧ ШЩ ЪЫЬ Э Ю Я'.split(),
    'de': 'AÄ B C D E F G H I J K L M N OÖ P Q R Sß T UÜ V W X Y Z'.split(),
}


def alphabet_data(russian, latin, glyphs):
    output = []
    table = []
    for tag, mapping, bitmap, font, other in (
        ('ru', russian, glyphs, 0, '…'),
        ('de', latin, {}, 3, 'MEHR'),
    ):
        keys = ALPHABET_KEYS[tag]
        if len(keys) != 26:
            raise ValueError(f'Easy Chat alphabet must have 26 letter keys: {tag}')
        buckets = [0] * 256
        for index, key in enumerate(keys, start=1):
            for char in key:
                for form in (char, char.lower()):
                    if form in mapping:
                        buckets[mapping[form]] = index
        output.append(demo.assembly_bytes(f'gLearnerEasyChatAlphabet_{tag}', buckets))
        labels = []
        for index, key in enumerate([other, *keys]):
            label = f'LearnerEasyChatKey_{tag}_{index}'
            # Umlaut variants share the corresponding plain Latin key.
            key_text = key[0] if tag == 'de' and index != 0 else key
            if tag == 'ru' and key == 'ЪЫЬ':
                key_text = 'Ы'
            width = 32 if index == 0 else 16
            output.append(demo.assembly_bytes(label, demo.message([key_text], mapping, bitmap, font, width)))
            labels.append(label)
        table.extend(labels)
    output.append('\t.balign 4\ngLearnerEasyChatKeys::\n'
                  + ''.join(f'\t.4byte {label}\n' for label in table))
    return output


def generate(russian, latin, glyphs):
    russian_groups = demo.validate.load(demo.ROOT / 'language_learning/easy_chat_ru.json')
    output = ['\t.balign 4\n']
    tables = []

    for index, group in enumerate(GROUPS):
        if group in ('pokemon', 'pokemon_2', 'move_1', 'move_2'):
            tables.append(['0', '0'])
            continue
        path = demo.ROOT / f'src/data/text/easy_chat/groups/{group}/words.h'
        source = path.read_text(encoding='utf-8')
        english, german = re.split(r'#elif GERMAN', source, maxsplit=1)
        english = re.findall(r'"([^"]*)\$"', english)
        german = [word.replace('{POKEBLOCK}', 'POKéRIEGEL')
                  for word in re.findall(r'"([^"]*)\$"', german)]
        russian_words = russian_groups.get(group)
        if len(english) != len(german) or (russian_words is not None and len(russian_words) != len(english)):
            raise ValueError(f'Easy Chat word IDs differ for {group}')
        tables.append([])
        for tag, words, mapping, bitmap, font in (
            ('ru', russian_words, russian, glyphs, 0),
            ('de', german, latin, {}, 3),
        ):
            labels = []
            for word_index, word in enumerate(words or []):
                label = f'LearnerEasyChat_{tag}_{index}_{word_index}'
                if len(demo.wrap(word, mapping, bitmap, 104)) != 1:
                    raise ValueError(f'Easy Chat label exceeds its half-line: {tag}/{group}/{word_index}')
                output.append(demo.assembly_bytes(label, demo.message([word], mapping, bitmap, font, 104)))
                labels.append(label)
            if labels:
                group_label = f'LearnerEasyChat_{tag}_{index}'
                output.append('\t.balign 4\n' + group_label + ':\n'
                              + ''.join(f'\t.4byte {label}\n' for label in labels))
                tables[-1].append(group_label)
            else:
                tables[-1].append('0')
    output.append('\t.balign 4\ngLearnerEasyChatWords::\n'
                  + ''.join(f'\t.4byte {ru}, {de}\n' for ru, de in tables))
    output.extend(alphabet_data(russian, latin, glyphs))
    return output
