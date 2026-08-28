#!/usr/bin/env python3
"""Compile the two welcome lessons into an ignored, ROM-native assembly file."""

import json
import re
from pathlib import Path

import validate

ROOT = Path(__file__).resolve().parents[2]
DIALOGUE_ID = "littleroot.player_house.mom.welcome.001"
MAX_LINE_WIDTH = 200  # Conservative margin inside the game's 216px message area.
MAX_MESSAGE_BYTES = 256  # gStringVar4 in src/text.c; includes controls and EOS.
SEMICOLON_ROWS = ['00', '00', '01', '00', '00', '01', '01', '10', '00']


def load_font():
    font = json.loads((ROOT / "language_learning/fonts/cyrillic.json").read_text(encoding="utf-8"))
    glyphs = font["glyphs"]
    start = font["first_code"]
    if start != 0x87 or len(glyphs) > len(glyph_codes()):
        raise ValueError("Cyrillic glyphs exceed unused Latin slots")
    for char, rows in glyphs.items():
        if len(char) != 1 or len(rows) != 9 or not 1 <= len(rows[0]) <= 7:
            raise ValueError(f"Invalid glyph dimensions: {char}")
        if any(len(row) != len(rows[0]) or set(row) - {"0", "1"} for row in rows):
            raise ValueError(f"Invalid bitmap: {char}")
    return start, glyphs


def load_charmap():
    # Read only the Latin section. Japanese shares byte values but uses another font.
    text = (ROOT / "charmap.txt").read_text(encoding="utf-8").split("@ Hiragana")[0]
    mapping = {}
    for line in text.splitlines():
        match = re.fullmatch(r"'(.+)'\s*=\s*([0-9A-F]{2})\s*", line)
        if match:
            char = match[1].replace("\\'", "'")
            if len(char) == 1 and char != "$":
                mapping[char] = int(match[2], 16)
    return mapping


def encode(text, mapping):
    try:
        return [mapping[c] for c in text]
    except KeyError as exc:
        raise ValueError(f"Unsupported ROM character: {exc.args[0]!r}") from exc


def glyph_codes():
    text = (ROOT / "charmap.txt").read_text(encoding="utf-8").split("@ Hiragana")[0]
    used = {int(x, 16) for line in text.splitlines() if "=" in line
            for x in re.findall(r"\b[0-9A-F]{2}\b", line.split("=", 1)[1])}
    preferred = list(range(0x87, 0xA0))
    return preferred + [i for i in range(1, 0xF0) if i not in used and i not in preferred]


def russian_mapping(latin, glyphs):
    return dict(latin, **dict(zip(glyphs, glyph_codes())))


def dictionary_entry(item):
    lemma = item.get("dictionary_form", item["lemma"])
    return f"{lemma}: {item['english']}"


def wrap(text, mapping, glyphs, max_width=MAX_LINE_WIDTH):
    if not text or any(c in text for c in "\n\r\t${}"):
        raise ValueError("Expected plain, nonempty lesson text without control codes")
    encode(text, mapping)  # Never silently drop unsupported characters.
    def width(word):
        return sum(len(glyphs[c][0]) + 1 if c in glyphs else 8 for c in word)
    lines = []
    current = ""
    for word in text.split():
        if width(word) > max_width:
            raise ValueError(f"Word exceeds message width: {word}")
        candidate = f"{current} {word}" if current else word
        if width(candidate) > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    lines.append(current)
    return lines


def message(pages, mapping, glyphs, font, max_width=MAX_LINE_WIDTH):
    # Explicit Latin mode + font selection, then restore the window's default font.
    data = [0xFC, 0x16, 0xFC, 0x06, font]
    # The native page arrow expects the shadowed font's tile format.
    page_break = [0xFC, 0x06, 3, 0xFB, 0xFC, 0x06, font]
    for page_index, page in enumerate(pages):
        if page_index:
            data.extend(page_break)
        for line_index, line in enumerate(wrap(page, mapping, glyphs, max_width)):
            if line_index:
                data.extend([0xFE] if line_index % 2 else page_break)
            for char in line:
                # The stock semicolon resembles an icon. Use our font-0 bitmap
                # in both languages, then restore the surrounding text font.
                if char == ';' and font != 0:
                    data.extend([0xFC, 0x06, 0, mapping[char], 0xFC, 0x06, font])
                else:
                    data.extend(encode(char, mapping))
    data.extend([0xFC, 0x07, 0xFF])
    if len(data) > MAX_MESSAGE_BYTES:
        raise ValueError("Lesson exceeds the game's message buffer safety limit")
    return data


def encode_glyph(rows):
    # The variable-width font-0 renderer reads the LEFT pixel from bit 7.
    return [0, 0, 0] + [int(row.ljust(8, "0"), 2) for row in rows] + [0] * 4


def assembly_bytes(label, data):
    lines = [f"{label}::"]
    for i in range(0, len(data), 16):
        lines.append("\t.byte " + ", ".join(f"0x{x:02X}" for x in data[i:i + 16]))
    return "\n".join(lines) + "\n"


def generate():
    validate.main()
    start, glyphs = load_font()
    latin = load_charmap()
    russian = russian_mapping(latin, glyphs)
    parts = [
        '#include "constants/vars.h"\n#include "constants/script_menu.h"\n',
        '\t.include "include/macros.inc"\n\t.include "include/macros/event.inc"\n',
        '\t.section .learner_demo, "a", %progbits\n',
        '\t.include "language_learning/integration/lesson_script.inc"\n',
    ]
    for tag, prefix, mapping, font in [("ru", "Ru", russian, 0), ("de", "De", latin, 3)]:
        pack = validate.load(ROOT / f"language_learning/language_packs/{tag}/pack.json")
        dialogue = next(d for d in pack["dialogues"] if d["dialogue_id"] == DIALOGUE_ID)
        variant = next(v for v in dialogue["variants"] if v["id"] == "expanded")
        words = {v["id"]: v for v in pack["vocabulary"]}
        pages = [dictionary_entry(words[k]) for k in variant["vocabulary_ids"]]
        parts.append(assembly_bytes(f"LearnerLesson_{prefix}Text", message([variant["text"]], mapping, glyphs, font)))
        parts.append(assembly_bytes(f"LearnerLesson_{prefix}Hint", message([variant["english_gloss"]], latin, {}, 3)))
        parts.append(assembly_bytes(f"LearnerLesson_{prefix}Words", message(pages, mapping, glyphs, font)))
    import opening
    parts.extend(opening.generate(russian, latin, glyphs))
    import ui
    parts.extend(ui.generate(russian, latin, glyphs))
    indices = [255] * 256
    for index, code in enumerate(glyph_codes()[:len(glyphs)]):
        indices[code] = index
    indices[latin[';']] = len(glyphs)
    parts.append(assembly_bytes("gLearnerGlyphIndex", indices))
    bitmap = []
    for rows in glyphs.values():
        bitmap.extend(encode_glyph(rows))
    bitmap.extend(encode_glyph(SEMICOLON_ROWS))
    parts.append(assembly_bytes("gLearnerGlyphs", bitmap))
    parts.append(assembly_bytes("gLearnerGlyphWidths", [len(rows[0]) + 1 for rows in glyphs.values()] + [3]))
    parts.append(assembly_bytes("gLearnerGlyphCount", [len(glyphs) + 1]))
    return "\n".join(parts)


def main():
    output = ROOT / "build/learner_demo/lesson.s"
    output.parent.mkdir(parents=True, exist_ok=True)
    content = generate()
    if not output.exists() or output.read_text(encoding="utf-8") != content:
        output.write_text(content, encoding="utf-8", newline="\n")
    print(f"Generated bilingual lesson: {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
