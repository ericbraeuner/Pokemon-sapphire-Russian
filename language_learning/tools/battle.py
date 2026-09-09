"""Encode battle templates without treating battle placeholders as field variables."""
import re
import build_demo as demo

TOKENS = {'ATTACKING_MON': [0xFD, 12], 'DEFENDING_MON': [0xFD, 13],
          'UNKNOWN_A': [0xFC, 10], 'PAUSE_UNTIL_PRESS': [0xFC, 9],
          'MENU_COLORS': [0xFC, 5, 5, 0xFC, 4, 13, 14, 15],
          'COLUMN': [0xFC, 19, 46], 'FLEE': [0xFC, 16, 17, 0],
          'POKEBLOCK': [0x55, 0x56, 0x57, 0x58, 0x59],
          'PLAY_SE SE_FLEE': [0xFC, 0x10, 0x11, 0],
          'PLAY_SE SE_DING_DONG': [0xFC, 0x10, 0x49, 0],
          'PLAY_SE SE_BALL_BOUNCE_1': [0xFC, 0x10, 0x38, 0],
          'PLAY_BGM MUS_CAUGHT': [0xFC, 0x0B, 0x60, 1],
          'PALETTE 5': [0xFC, 5, 5],
          'COLOR_HIGHLIGHT_SHADOW SKY_BLUE LIGHT_BLUE WHITE2': [0xFC, 4, 13, 14, 15],
          'CLEAR_TO 0x2E': [0xFC, 0x13, 0x2E],
          'HIGHLIGHT RED': [0xFC, 2, 2],
          'HIGHLIGHT TRANSPARENT': [0xFC, 2, 0],
          'RIGHT_ARROW': [0x7C]}


def validate_line_width(text, glyphs, max_width=demo.MAX_LINE_WIDTH):
    """Reject literal text that cannot fit even before runtime names expand."""
    for line in re.split(r'\\[npl]', text):
        literal = re.sub(r'\{[^}]+\}', '', line)
        width = sum(len(glyphs[c][0]) + 1 if c in glyphs else 8 for c in literal)
        if width > max_width:
            raise ValueError('Battle text literal exceeds message width')

def encode(text, mapping, font, fragment=False):
    data = [] if fragment else [0xFC, 22, 0xFC, 6, font]
    for part in re.split(r'(\{[^}]+\}|\\[npl])', text):
        if part.startswith('{'):
            token = part[1:-1]
            if re.fullmatch(r'STRING \d+', token):
                number = int(token.split()[1])
                if number > 52:
                    raise ValueError('Invalid battle placeholder')
                data.extend([0xFD, number])
            elif re.fullmatch(r'PAUSE \d+', token):
                data.extend([0xFC, 8, int(token.split()[1])])
            else:
                data.extend(TOKENS[token])
        elif part in (r'\n', r'\p', r'\l'):
            code = {r'\n': 0xFE, r'\p': 0xFB, r'\l': 0xFA}[part]
            data.extend([code] if code == 0xFE else [0xFC, 6, 3, code, 0xFC, 6, font])
        else:
            data.extend(demo.encode(part, mapping))
    if not fragment:
        data.extend([0xFC, 7])
    data.append(0xFF)
    if len(data) > 240:
        raise ValueError('Battle template too long')
    return data

def generate(russian, latin):
    entries = demo.validate.load(demo.ROOT / 'language_learning/battle.json')
    source = (demo.ROOT / 'src/data/battle_strings_en.h').read_text()
    parts, table = [], []
    cyrillic = demo.load_font()[1]
    for index, (symbol, entry) in enumerate(entries.items()):
        if not re.fullmatch(r'Battle(?:Stat)?Text_\w+', symbol) or not re.search(r'const u8 ' + symbol + r'\[\]', source):
            raise ValueError(f'Unknown battle source: {symbol}')
        labels = []
        for tag, mapping, font in [('ru', russian, 0), ('de', latin, 3)]:
            validate_line_width(entry[tag], cyrillic if tag == 'ru' else {})
            label = f'LearnerBattle_{index}_{tag}'
            parts.append(demo.assembly_bytes(label, encode(entry[tag], mapping, font, entry.get('fragment', False))))
            labels.append(label)
        table.append('\t.4byte ' + ', '.join([symbol] + labels))
    names = demo.validate.load(demo.ROOT / 'language_learning/battle_names.json')
    for index, (symbol, entry) in enumerate(names.items()):
        if re.fullmatch(r'MOVE_[A-Z0-9_]+', symbol):
            pointer = f'gMoveNames + 13 * {symbol}'
        elif re.fullmatch(r'TYPE_[A-Z0-9_]+', symbol):
            pointer = f'gTypeNames + 7 * {symbol}'
        else:
            raise ValueError('Invalid battle name constant')
        labels = []
        for tag, mapping, font in [('ru', russian, 0), ('de', latin, 3)]:
            bitmap = demo.load_font()[1] if tag == 'ru' else {}
            width = 72 if symbol.startswith('MOVE_') else 40
            if len(demo.wrap(entry[tag], mapping, bitmap, width)) != 1:
                raise ValueError(f'Battle name too wide: {symbol}/{tag}')
            label = f'LearnerBattleName_{index}_{tag}'
            parts.append(demo.assembly_bytes(label, encode(entry[tag], mapping, font)))
            labels.append(label)
        table.append('\t.4byte ' + ', '.join([pointer] + labels))
    parts.insert(0, '#include "constants/moves.h"\n#include "constants/pokemon.h"\n')
    return parts, table
