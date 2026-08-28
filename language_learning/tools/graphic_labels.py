"""Compile localized menu tiles from existing indexed art and native bitmap fonts.

Only label interiors change. Tile indices, palette indices, borders and animation
maps stay intact. Generated graphics live in the ignored learner assembly.
"""
from PIL import Image
import build_demo as demo

SHEETS = {
    'bag': ('graphics/interface/bag_screen.png', 'BagTiles', (256, 64)),
    'dex_search': ('graphics/pokedex/menu_search.png', 'DexSearchTiles', (128, 64)),
    'dex_main': ('graphics/pokedex/menu.png', 'DexMainTiles', (256, 96)),
    'dex_sprites': ('graphics/pokedex/menu2.png', 'DexSpriteTiles', (64, 248)),
}


def glyph(char, latin, cyrillic, font):
    if char in cyrillic:
        rows = cyrillic[char]
        # Match the stock font's baseline at row 12.
        return [[0] * len(rows[0])] * 4 + [[int(p) for p in row] for row in rows]
    if char == ' ':
        return [[0] * 3 for _ in range(13)]
    code = latin[char]
    tile = font.crop((code % 16 * 8, code // 16 * 16,
                      code % 16 * 8 + 8, code // 16 * 16 + 16))
    bounds = tile.getbbox()
    if bounds is None:
        raise ValueError(f'No bitmap for {char!r}')
    if bounds[3] > 13:
        raise ValueError(f'Glyph extends below the graphic label baseline: {char!r}')
    return [[int(tile.getpixel((x, y)) != 0) for x in range(bounds[2])]
            for y in range(13)]


def render(kind, tag):
    path, _, size = SHEETS[kind]
    with Image.open(demo.ROOT / path) as source:
        sheet = source.copy()
    if sheet.mode != 'P' or sheet.size != size:
        raise ValueError('Unexpected source tile sheet')
    with Image.open(demo.ROOT / 'graphics/fonts/font0_lat.png') as source:
        font = source.copy()
    latin = demo.load_charmap()
    _, cyrillic = demo.load_font()
    entries = demo.validate.load(demo.ROOT / 'language_learning/graphic_labels.json')[kind]
    for entry in entries:
        x, y = entry['x'], entry['y']
        if kind == 'bag':
            left, top, width, height, background, ink = x, y + 1, 64, 14, 10, 15
        elif kind == 'dex_search':
            left, top, width, height, background, ink = x + 5, y + 2, 31, 12, entry['background'], 4
        else:
            left, top, width, height, background, ink = x, y, entry['width'], 16, entry['background'], entry['ink']
        if left < 0 or top < 0 or left + width > size[0] or top + height > size[1]:
            raise ValueError('Label outside tile sheet')
        letters = [glyph(c, latin, cyrillic if tag == 'ru' else {}, font) for c in entry[tag]]
        text_width = sum(len(g[0]) + 1 for g in letters) - 1
        if text_width > width:
            raise ValueError(f'Graphic label overflow: {kind}/{tag}/{entry[tag]}')
        sheet.paste(background, (left, top, left + width, top + height))
        cursor = left + (width - text_width) // 2
        for letter in letters:
            for gy, row in enumerate(letter):
                for gx, bit in enumerate(row):
                    if bit:
                        if not top <= y + gy < top + height:
                            raise ValueError('Glyph exceeds label height')
                        sheet.putpixel((cursor + gx, y + gy), ink)
            cursor += len(letter[0]) + 1
    return sheet


def tile_bytes(sheet):
    data = []
    for ty in range(0, sheet.height, 8):
        for tx in range(0, sheet.width, 8):
            for y in range(8):
                for x in range(0, 8, 2):
                    lo, hi = sheet.getpixel((tx + x, ty + y)), sheet.getpixel((tx + x + 1, ty + y))
                    if not 0 <= lo < 16 or not 0 <= hi < 16:
                        raise ValueError('Not a 4-bit palette')
                    data.append(lo | hi << 4)
    return data


def literal_lz(data):
    """GBA LZ77 stream with literal-only groups; valid for sprite sheet loaders."""
    result = [0x10, len(data) & 255, len(data) >> 8 & 255, len(data) >> 16]
    for i in range(0, len(data), 8):
        result.extend([0] + data[i:i + 8])
    result.extend([0] * (-len(result) % 4))
    return result


def generate():
    parts = []
    for kind, (_, name, _) in SHEETS.items():
        for tag in ('ru', 'de'):
            data = tile_bytes(render(kind, tag))
            if kind == 'dex_sprites':
                data = literal_lz(data)
            parts.append('\t.balign 4\n' + demo.assembly_bytes(
                'gLearner' + name + tag.title(), data))
    return parts
