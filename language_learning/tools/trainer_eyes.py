"""Compile indexed, four-line Trainer Eyes descriptions."""
import re

import build_demo as demo


SOURCE_PATTERN = re.compile(
    r'static const u8 (TrainerEyeDescription_\w+)\[\] = _\(\s*((?:"[^"]*"\s*)+)\);')


def load_source(name):
    source = (demo.ROOT / 'src/data/text' / name).read_text(encoding='utf-8')
    result = {}
    order = []
    for symbol, body in SOURCE_PATTERN.findall(source):
        lines = [line.removesuffix('$') for line in re.findall(r'"([^"]*)"', body)]
        if len(lines) != 4:
            raise ValueError(f'{symbol} does not contain four Trainer Eyes lines')
        order.append(symbol)
        result[symbol] = lines
    return order, result


def compile_description(label, lines, mapping, glyphs, font, max_width):
    data = []
    for line in lines:
        if len(demo.wrap(line, mapping, glyphs, max_width)) != 1:
            raise ValueError(f'{label} line exceeds the Trainer Eyes panel: {line}')
        data.extend(demo.message([line], mapping, glyphs, font, max_width=max_width))
    return demo.assembly_bytes(label, data)


def generate(russian, latin, glyphs):
    order, english = load_source('trainer_eye_descriptions_en.h')
    german_order, german = load_source('trainer_eye_descriptions_de.h')
    translations = demo.validate.load(demo.ROOT / 'language_learning/trainer_eyes.json')
    if order != german_order or not set(translations) <= set(english):
        raise ValueError('Trainer Eyes catalogues do not agree')
    parts = []
    table = []
    for index, symbol in enumerate(order):
        if symbol not in translations:
            table.append('\t.4byte 0, 0')
            continue
        ru_label = f'LearnerTrainerEyes_{index}_ru'
        de_label = f'LearnerTrainerEyes_{index}_de'
        parts.append(compile_description(ru_label, translations[symbol], russian, glyphs, 0, 136))
        # The official German catalogue already targets this panel; the simple
        # generator models Latin glyphs as eight pixels even though the ROM font
        # is narrower, so retain the source layout with its original line breaks.
        parts.append(compile_description(de_label, german[symbol], latin, {}, 3, 256))
        table.append(f'\t.4byte {ru_label}, {de_label}')
    parts.append('\t.balign 4\ngLearnerTrainerEyeDescriptions::\n' + '\n'.join(table))
    parts.append(f'gLearnerTrainerEyeDescriptionCount::\n\t.2byte {len(order)}\n')
    return parts
