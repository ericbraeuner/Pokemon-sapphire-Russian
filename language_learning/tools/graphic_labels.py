"""Compile localized menu tiles from existing indexed art and native bitmap fonts.

Only label interiors change. Tile indices, palette indices, borders and animation
maps stay intact. Generated graphics live in the ignored learner assembly.
"""
from collections import Counter

from PIL import Image
import build_demo as demo

SHEETS = {
    'bag': ('graphics/interface/bag_screen.png', 'BagTiles', (256, 64)),
    'dex_search': ('graphics/pokedex/menu_search.png', 'DexSearchTiles', (128, 64)),
    'dex_main': ('graphics/pokedex/menu.png', 'DexMainTiles', (256, 96)),
    'dex_sprites': ('graphics/pokedex/menu2.png', 'DexSpriteTiles', (64, 248)),
    'storage_misc': ('graphics/pokemon_storage/misc1.png', 'StorageMiscTiles', (72, 88)),
    'summary': ('graphics/interface/status_screen.png', 'SummaryTiles', (128, 112)),
    'money': ('graphics/interface/money.png', 'MoneyTiles', (32, 16)),
    'party_misc': ('graphics/interface/party_menu_misc.png', 'PartyMiscTiles', (128, 64)),
}

TYPE_ICON_NAMES = (
    'normal', 'fight', 'flying', 'poison', 'ground', 'rock', 'bug',
    'ghost', 'steel', 'mystery', 'fire', 'water', 'grass', 'electric',
    'psychic', 'ice', 'dragon', 'dark', 'contest_cool', 'contest_beauty',
    'contest_cute', 'contest_smart', 'contest_tough',
)

STATUS_ICON_NAMES = ('poison', 'paralysis', 'sleep', 'freeze', 'burn', 'pokerus', 'faint')
BATTLE_STATUS_FILES = ('psn', 'par', 'slp', 'frz', 'brn')


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


def small_glyph(char, latin, cyrillic, font):
    if char == ' ':
        return [[0] * 2 for _ in range(7)]
    if char in cyrillic:
        rows = [[int(pixel) for pixel in row] for row in cyrillic[char]]
        source = Image.new('1', (len(rows[0]), len(rows)))
        for y, row in enumerate(rows):
            for x, pixel in enumerate(row):
                source.putpixel((x, y), pixel)
    else:
        code = latin[char]
        source = font.crop((code % 16 * 8, code // 16 * 16,
                            code % 16 * 8 + 8, code // 16 * 16 + 16))
    bounds = source.getbbox()
    if bounds is None:
        raise ValueError(f'No small bitmap for {char!r}')
    source = source.crop(bounds)
    width = max(1, round(source.width * min(1, 7 / source.height)))
    height = min(7, source.height)
    tile = source.resize((width, height), Image.Resampling.NEAREST)
    return [[int(tile.getpixel((x, y)) != 0) for x in range(tile.width)]
            for y in range(tile.height)]


def render(kind, tag):
    path, _, size = SHEETS[kind]
    with Image.open(demo.ROOT / path) as source:
        sheet = source.copy()
    if kind in ('storage_misc', 'summary') and sheet.mode == 'L':
        # gbagfx assigns grayscale ramps in reverse palette order.
        sheet = sheet.point(lambda value: 15 - value // 17).convert('P')
    if sheet.mode != 'P' or sheet.size != size:
        raise ValueError('Unexpected source tile sheet')
    with Image.open(demo.ROOT / 'graphics/fonts/font0_lat.png') as source:
        font = source.copy()
    latin = demo.load_charmap()
    _, cyrillic = demo.load_font()
    entries = demo.validate.load(demo.ROOT / 'language_learning/graphic_labels.json')[kind]
    for entry in entries:
        x, y = entry['x'], entry['y']
        if 'bottom_x' in entry:
            label = Image.new('P', (24, 16))
            label.putpalette(sheet.getpalette())
            label.paste(sheet.crop((x, y, x + 24, y + 8)), (0, 0))
            label.paste(sheet.crop((entry['bottom_x'], y + 8, entry['bottom_x'] + 24, y + 16)), (0, 8))
            label.paste(12, (0, 3, 24, 14))
            letters = []
            for char in entry[tag]:
                rows = glyph(char, latin, cyrillic if tag == 'ru' else {}, font)
                occupied = [row for row in rows if any(row)]
                letters.append(occupied or [[0] * len(rows[0])])
            text_width = sum(len(g[0]) + 1 for g in letters) - 1
            if text_width > 24 or any(len(g) > 11 for g in letters):
                raise ValueError(f'Navbar label overflow: {tag}/{entry[tag]}')
            cursor = (24 - text_width) // 2
            for letter in letters:
                top_row = 3 + (11 - len(letter)) // 2
                for gy, row in enumerate(letter):
                    for gx, bit in enumerate(row):
                        if bit:
                            label.putpixel((cursor + gx, top_row + gy), 15)
                cursor += len(letter[0]) + 1
            sheet.paste(label.crop((0, 0, 24, 8)), (x, y))
            sheet.paste(label.crop((0, 8, 24, 16)), (entry['bottom_x'], y + 8))
            continue
        if kind == 'bag':
            left, top, width, height, background, ink = x, y + 1, 64, 14, 10, 15
        elif kind == 'dex_search':
            left, top, width, height, background, ink = x + 5, y + 2, 31, 12, entry['background'], 4
        elif kind == 'summary':
            left, top = x, y
            width, height = entry['width'], 8
            background, ink = entry.get('background', 6), entry.get('ink', 2)
        elif kind == 'money':
            left, top = x, y
            width, height = entry['width'], 10
            background, ink = entry.get('background', 6), entry.get('ink', 14)
        else:
            left, top, width, height = x, y, entry['width'], entry.get('height', 16)
            background, ink = entry['background'], entry['ink']
        if left < 0 or top < 0 or left + width > size[0] or top + height > size[1]:
            raise ValueError('Label outside tile sheet')
        glyph_fn = small_glyph if kind in ('summary', 'money', 'party_misc') else glyph
        letters = [glyph_fn(c, latin, cyrillic if tag == 'ru' else {}, font) for c in entry[tag]]
        text_width = sum(len(g[0]) + 1 for g in letters) - 1
        if text_width > width:
            raise ValueError(f'Graphic label overflow: {kind}/{tag}/{entry[tag]}')
        sheet.paste(background, (left, top, left + width, top + height))
        cursor = left + (width - text_width) // 2
        for letter in letters:
            label_y = top + (height - len(letter)) // 2
            for gy, row in enumerate(letter):
                for gx, bit in enumerate(row):
                    if bit:
                        if not top <= label_y + gy < top + height:
                            raise ValueError('Glyph exceeds label height')
                        sheet.putpixel((cursor + gx, label_y + gy), ink)
            cursor += len(letter[0]) + 1
    return sheet


def render_area_unknown(tag):
    """Return the three 32x32 animated pieces of the Area Unknown sign."""
    with Image.open(demo.ROOT / 'graphics/pokedex/area_unknown.png') as source:
        sheet = source.copy()
    if sheet.mode != 'P' or sheet.size != (32, 96):
        raise ValueError('Unexpected Area Unknown sign sheet')
    combined = Image.new('P', (96, 32))
    combined.putpalette(sheet.getpalette())
    for index in range(3):
        combined.paste(sheet.crop((0, index * 32, 32, index * 32 + 32)), (index * 32, 0))
    with Image.open(demo.ROOT / 'graphics/fonts/font0_lat.png') as source:
        font = source.copy()
    latin = demo.load_charmap()
    _, cyrillic = demo.load_font()
    labels = {'ru': 'НЕИЗВ.', 'de': 'UNBEK.'}
    letters = [glyph(char, latin, cyrillic if tag == 'ru' else {}, font) for char in labels[tag]]
    text_width = sum(len(letter[0]) + 1 for letter in letters) - 1
    if text_width > 80:
        raise ValueError(f'Area Unknown label overflow: {tag}/{labels[tag]}')
    combined.paste(15, (8, 7, 88, 25))
    cursor = 8 + (80 - text_width) // 2
    for letter in letters:
        top = 7 + (18 - len(letter)) // 2
        for y, row in enumerate(letter):
            for x, bit in enumerate(row):
                if bit:
                    combined.putpixel((cursor + x, top + y), 0)
        cursor += len(letter[0]) + 1
    result = Image.new('P', (32, 96))
    result.putpalette(sheet.getpalette())
    for index in range(3):
        result.paste(combined.crop((index * 32, 0, index * 32 + 32, 32)), (0, index * 32))
    return result


def render_type_icons(tag):
    """Replace only the lettering in the shared 32x16 type/category sprites."""
    entries = demo.validate.load(demo.ROOT / 'language_learning/graphic_labels.json')['type_icons']
    if tuple(entry['name'] for entry in entries) != TYPE_ICON_NAMES:
        raise ValueError('Type icon order differs from the sprite animation table')
    with Image.open(demo.ROOT / 'graphics/fonts/font0_lat.png') as source:
        font = source.copy()
    latin = demo.load_charmap()
    _, cyrillic = demo.load_font()
    sheet = Image.new('P', (32, 16 * len(entries)))
    for index, entry in enumerate(entries):
        with Image.open(demo.ROOT / f'graphics/types/{entry["name"]}.png') as source:
            icon = source.copy()
        if icon.mode != 'P' or icon.size != (32, 16):
            raise ValueError(f'Unexpected type icon: {entry["name"]}')
        if index == 0:
            sheet.putpalette(icon.getpalette())
        if entry['name'] != 'mystery':
            colors = Counter(icon.getpixel((x, y)) for y in range(4, 12)
                             for x in range(1, 31))
            body = max((color for color in colors if color not in (0, 14, 15)),
                       key=colors.get)
            for y in range(4, 12):
                for x in range(1, 31):
                    if icon.getpixel((x, y)) in (14, 15):
                        icon.putpixel((x, y), body)
            letters = [small_glyph(char, latin, cyrillic if tag == 'ru' else {}, font)
                       for char in entry[tag]]
            width = sum(len(letter[0]) + 1 for letter in letters) - 1
            if width > 29:
                raise ValueError(f'Type icon label overflow: {tag}/{entry["name"]}')
            cursor = (32 - width) // 2
            for letter in letters:
                top = 4 + (7 - len(letter)) // 2
                for gy, row in enumerate(letter):
                    for gx, bit in enumerate(row):
                        if bit:
                            icon.putpixel((cursor + gx + 1, top + gy + 1), 14)
                            icon.putpixel((cursor + gx, top + gy), 15)
                cursor += len(letter[0]) + 1
        sheet.paste(icon, (0, index * 16))
    return sheet


def draw_status_label(sheet, x0, y0, width, label, background, latin, cyrillic, font):
    sheet.paste(background, (x0, y0 + 1, x0 + width, y0 + 7))
    letters = [small_glyph(char, latin, cyrillic, font) for char in label]
    text_width = sum(len(letter[0]) + 1 for letter in letters) - 1
    if text_width > width:
        raise ValueError(f'Status icon label overflow: {label}')
    cursor = x0 + (width - text_width) // 2
    for letter in letters:
        height = min(6, len(letter))
        glyph_image = Image.new('1', (len(letter[0]), len(letter)))
        for gy, row in enumerate(letter):
            for gx, bit in enumerate(row):
                glyph_image.putpixel((gx, gy), bit)
        if glyph_image.height != height:
            glyph_image = glyph_image.resize((glyph_image.width, height), Image.Resampling.NEAREST)
        top = y0 + 1 + (6 - height) // 2
        for gy in range(height):
            for gx in range(glyph_image.width):
                if glyph_image.getpixel((gx, gy)):
                    sheet.putpixel((cursor + gx, top + gy), 2)
        cursor += len(letter[0]) + 1


def render_status_icons(tag):
    """Replace lettering in the shared Party/Summary status tiles."""
    entries = demo.validate.load(demo.ROOT / 'language_learning/graphic_labels.json')['status_icons']
    if tuple(entry['name'] for entry in entries) != STATUS_ICON_NAMES:
        raise ValueError('Status icon order differs from the sprite animation table')
    with Image.open(demo.ROOT / 'graphics/interface/status_icons.png') as source:
        sheet = source.copy()
    if sheet.mode != 'P' or sheet.size != (32, 56):
        raise ValueError('Unexpected status icon sheet')
    with Image.open(demo.ROOT / 'graphics/fonts/font0_lat.png') as source:
        font = source.copy()
    latin = demo.load_charmap()
    _, cyrillic = demo.load_font()
    for index, entry in enumerate(entries):
        y0 = index * 8
        draw_status_label(sheet, 8, y0, 16, entry[tag], sheet.getpixel((16, y0)),
                          latin, cyrillic if tag == 'ru' else {}, font)
    return sheet


def render_battle_status_icons(tag):
    """Return five raw 24x8 status badges in health-box tile order."""
    entries = demo.validate.load(demo.ROOT / 'language_learning/graphic_labels.json')['status_icons']
    if tuple(entry['name'] for entry in entries) != STATUS_ICON_NAMES:
        raise ValueError('Status icon order differs from the sprite animation table')
    with Image.open(demo.ROOT / 'graphics/fonts/font0_lat.png') as source:
        font = source.copy()
    latin = demo.load_charmap()
    _, cyrillic = demo.load_font()
    sheet = Image.new('P', (24, 40))
    for index, entry in enumerate(entries[:5]):
        with Image.open(demo.ROOT / f'graphics/battle_interface/status_{BATTLE_STATUS_FILES[index]}.png') as source:
            icon = source.copy()
        if icon.mode != 'P' or icon.size != (24, 8):
            raise ValueError(f'Unexpected battle status icon: {entry["name"]}')
        if index == 0:
            sheet.putpalette(icon.getpalette())
        draw_status_label(icon, 3, 0, 15, entry[tag], 12,
                          latin, cyrillic if tag == 'ru' else {}, font)
        sheet.paste(icon, (0, index * 8))
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
            if kind in ('dex_sprites', 'storage_misc', 'summary', 'money', 'party_misc'):
                data = literal_lz(data)
            parts.append('\t.balign 4\n' + demo.assembly_bytes(
                'gLearner' + name + tag.title(), data))
    for tag in ('ru', 'de'):
        data = literal_lz(tile_bytes(render_area_unknown(tag)))
        parts.append('\t.balign 4\n' + demo.assembly_bytes(
            'gLearnerAreaUnknownTiles' + tag.title(), data))
        data = literal_lz(tile_bytes(render_type_icons(tag)))
        parts.append('\t.balign 4\n' + demo.assembly_bytes(
            'gLearnerMoveTypeTiles' + tag.title(), data))
        data = literal_lz(tile_bytes(render_status_icons(tag)))
        parts.append('\t.balign 4\n' + demo.assembly_bytes(
            'gLearnerStatusIconTiles' + tag.title(), data))
        data = tile_bytes(render_battle_status_icons(tag))
        parts.append('\t.balign 4\n' + demo.assembly_bytes(
            'gLearnerBattleStatusTiles' + tag.title(), data))
    return parts
