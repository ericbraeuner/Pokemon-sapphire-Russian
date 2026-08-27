"""Run with python -m unittest discover -s language_learning/tests -v."""

import copy
import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
import build_demo as demo
import validate
import opening


class LessonTests(unittest.TestCase):
    def setUp(self):
        start, self.glyphs = demo.load_font()
        self.latin = demo.load_charmap()
        self.russian = demo.russian_mapping(self.latin, self.glyphs)

    def test_both_real_lessons_generate_deterministically(self):
        first = demo.generate()
        self.assertEqual(first, demo.generate())
        for language in ("Ru", "De"):
            for kind in ("Text", "Hint", "Words"):
                self.assertIn(f"LearnerLesson_{language}{kind}::", first)

    def test_russian_round_trip_and_font_restoration(self):
        phrase = "Привет! Добро пожаловать домой!"
        codes = demo.encode(phrase, self.russian)
        reverse = {value: key for key, value in self.russian.items()}
        self.assertEqual(phrase, "".join(reverse[code] for code in codes))
        encoded = demo.message([phrase], self.russian, self.glyphs, 0)
        self.assertEqual([0xFC, 0x16, 0xFC, 0x06, 0], encoded[:5])
        self.assertEqual([0xFC, 7, 0xFF], encoded[-3:])
        self.assertNotIn(0xFF, encoded[:-1])

    def test_german_special_characters_use_existing_glyphs(self):
        self.assertEqual([0xF1, 0xF2, 0xF3, 0xF4, 0xF5, 0xF6, 0x15], demo.encode("ÄÖÜäöüß", self.latin))

    def test_definition_separator_is_comma_not_rom_semicolon(self):
        self.assertEqual(demo.encode('home, house', self.latin), demo.encode('home; house', self.latin))
        self.assertNotIn(0x36, demo.encode('home; house', self.latin))

    def test_full_russian_alphabet_uses_only_unused_codes(self):
        alphabet = 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'
        self.assertEqual(set(alphabet + alphabet.lower()), set(self.glyphs))
        codes = [self.russian[c] for c in self.glyphs]
        self.assertEqual(len(codes), len(set(codes)))
        self.assertFalse(set(codes) & set(self.latin.values()))
        self.assertTrue(all(0 < c < 0xF0 for c in codes))

    def test_german_noun_dictionary_form_preserves_article(self):
        pack = validate.load(demo.ROOT / 'language_learning/language_packs/de/pack.json')
        item = next(word for word in pack['vocabulary'] if word['id'] == 'de.haus')
        self.assertEqual('das Haus: house', demo.dictionary_entry(item))
        phrase = next(word for word in pack['vocabulary'] if word['id'] == 'de.zuhause')
        self.assertTrue(demo.dictionary_entry(phrase).startswith('zu Hause:'))

    def test_opening_hooks_cover_both_houses_and_keep_base_text(self):
        paths = ['data/scripts/players_house.inc',
                 'data/maps/LittlerootTown_BrendansHouse_1F/scripts.inc',
                 'data/maps/LittlerootTown_MaysHouse_1F/scripts.inc']
        sources = '\n'.join((demo.ROOT / path).read_text(encoding='utf-8') for path in paths)
        for entry in opening.load()['dialogues']:
            hook = f"call LearnerOpening_{entry['id']}\n\t.else\n\tmsgbox {entry['base_symbol']}"
            self.assertIn(hook, sources)

    def test_all_opening_text_bands_and_dictionary_compile(self):
        assembly = '\n'.join(opening.generate(self.russian, self.latin, self.glyphs))
        for entry in opening.load()['dialogues']:
            for tag in ('ru', 'de'):
                for band in ('A1', 'A2', 'natural'):
                    self.assertIn(f"LearnerOpening_{entry['id']}_{tag}_{band}:", assembly)
        # Every assembly text emitted by opening.generate is independently bounded.
        for block in assembly.split('::\n')[1:]:
            byte_lines = []
            for line in block.splitlines():
                if not line.startswith('\t.byte '):
                    break
                byte_lines.extend(line[7:].split(', '))
            if byte_lines:
                self.assertLessEqual(len(byte_lines), demo.MAX_MESSAGE_BYTES)
                self.assertEqual('0xFF', byte_lines[-1])

    def test_font_bits_match_variable_width_renderer(self):
        for char, rows in self.glyphs.items():
            data = demo.encode_glyph(rows)
            self.assertEqual(16, len(data))
            for source, encoded in zip(rows, data[3:12]):
                rendered = "".join(str((encoded >> (7 - x)) & 1) for x in range(len(source)))
                self.assertEqual(source, rendered, char)
        self.assertEqual(0xF8, demo.encode_glyph(self.glyphs['П'])[3])

    def test_unknown_glyph_and_control_injection_rejected(self):
        for phrase in ("🙂", "Hello$", "{PLAYER}", "Hello\nworld"):
            with self.subTest(phrase=phrase), self.assertRaises(ValueError):
                demo.message([phrase], self.russian, self.glyphs, 0)

    def test_page_arrow_uses_native_shadowed_font(self):
        encoded = demo.message(["Привет", "дом"], self.russian, self.glyphs, 0)
        page = encoded.index(0xFB)
        self.assertEqual([0xFC, 6, 3, 0xFB, 0xFC, 6, 0], encoded[page - 3:page + 4])

    def test_wrapping_and_paging_prevent_overflow(self):
        phrase = "welcome " * 12
        lines = demo.wrap(phrase, self.latin, {})
        self.assertTrue(all(len(line) * 8 <= demo.MAX_LINE_WIDTH for line in lines))
        encoded = demo.message([phrase], self.latin, {}, 3)
        self.assertIn(0xFE, encoded)
        self.assertIn(0xFB, encoded)
        with self.assertRaises(ValueError):
            demo.message(["w" * 26], self.latin, {}, 3)
        with self.assertRaises(ValueError):
            demo.message(["hello world"] * 25, self.latin, {}, 3)

    def test_connected_catalogue_resolves_both_symbols(self):
        catalogue = validate.load(validate.ROOT / "integration/dialogue_catalog.json")
        validate.validate_sources(catalogue)
        for field, bad_value in [("symbol", "MissingSymbol"), ("base_text_symbol", "MissingText"), ("path", "../outside.inc")]:
            changed = copy.deepcopy(catalogue)
            changed["dialogues"][0]["source"][field] = bad_value
            with self.subTest(field=field), self.assertRaises(validate.ValidationError):
                validate.validate_sources(changed)


if __name__ == "__main__":
    unittest.main()
