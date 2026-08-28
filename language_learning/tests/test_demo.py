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
import ui


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

    def test_definition_separator_uses_corrected_semicolon_and_space(self):
        welcome = next(e for e in opening.load()['dialogues'] if e['id'] == 'Welcome')
        self.assertIn(['дом', 'home; house'], welcome['words']['ru'])
        self.assertEqual([0x36, self.latin[' ']], demo.encode('; ', self.latin))
        for font in (0, 3):
            data = demo.message(['home; house'], self.latin, {}, font)
            self.assertIn(0x36, data)
            if font == 3:
                self.assertIn(bytes([0xFC, 6, 0, 0x36, 0xFC, 6, 3, 0]), bytes(data))
        self.assertEqual(16, len(demo.encode_glyph(demo.SEMICOLON_ROWS)))

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
                 'data/maps/LittlerootTown/scripts.inc',
                 'data/maps/LittlerootTown_BrendansHouse_1F/scripts.inc',
                 'data/maps/LittlerootTown_MaysHouse_1F/scripts.inc']
        paths += ['data/scripts/tv.inc', 'data/maps/LittlerootTown_BrendansHouse_2F/scripts.inc',
                  'data/maps/LittlerootTown_MaysHouse_2F/scripts.inc',
                  'data/maps/LittlerootTown_ProfessorBirchsLab/scripts.inc']
        sources = '\n'.join((demo.ROOT / path).read_text(encoding='utf-8') for path in paths)
        for entry in opening.load()['dialogues']:
            self.assertIn(f"call LearnerOpening_{entry['id']}\n", sources)
            self.assertIn(f"\t.else\n\tmsgbox {entry['base_symbol']}", sources)

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

    def test_russian_capital_baselines_and_diaeresis(self):
        for char, rows in self.glyphs.items():
            if char.isupper():
                self.assertIn('1', rows[8], char)
        self.assertEqual(self.glyphs['е'][2:], self.glyphs['ё'][2:])
        self.assertEqual('01010', self.glyphs['ё'][0])

    def test_interface_translations_compile_and_have_declarations(self):
        entries = validate.load(demo.ROOT / 'language_learning/ui.json')
        header = (demo.ROOT / 'include/learner.h').read_text(encoding='utf-8')
        assembly = '\n'.join(ui.generate(self.russian, self.latin, self.glyphs))
        for key in entries:
            self.assertIn(f'LEARNER_DECLARE({key})', header)
            for tag in ('ru', 'de'):
                self.assertIn(f'LearnerUI_{tag}_{key}::', assembly)
        self.assertEqual('Да', entries['Yes']['ru'])
        self.assertEqual('Nein', entries['No']['de'])

    def test_naming_menu_cleanup_and_pending_language(self):
        source = (demo.ROOT / 'src/main_menu.c').read_text(encoding='utf-8')
        confirm = source.split('static void Task_NewGameSpeech25(u8 taskId)\n{')[1].split('static void Task_NewGameSpeech26')[0]
        self.assertEqual(2, confirm.count('Menu_DestroyCursor();'))
        self.assertIn('Menu_BlankWindowRect(left + 1, top + 1, left + 9, top + 2);', source)
        intro = (demo.ROOT / 'src/learner_intro.inc').read_text(encoding='utf-8')
        self.assertIn('sLearnerSettingsPending ? sLearnerLanguage : VarGet(VAR_LEARNER_LANGUAGE)', intro)
        naming = (demo.ROOT / 'src/naming_screen.c').read_text(encoding='utf-8')
        self.assertIn('namingScreenDataPtr->templateNum == 0 && Learner_GetLanguage()', naming)
        self.assertIn('LEARNER_UI(Learner_GetLanguage(), YourName)', naming)

    def test_rival_branch_rechecks_gender_after_help_menu(self):
        source = (demo.ROOT / 'data/maps/LittlerootTown_MaysHouse_2F/scripts.inc').read_text(encoding='utf-8')
        between = source.split('call_if_eq RivalsHouse_2F_EventScript_May\n')[1].split('call_if_eq RivalsHouse_2F_EventScript_Brendan')[0]
        self.assertIn('checkplayergender\n', between)

    def test_new_game_settings_committed_after_all_resets(self):
        code = (demo.ROOT / 'src/new_game.c').read_text(encoding='utf-8')
        function = code.split('void NewGameInitData(void)', 1)[1].split('#if DEBUG', 1)[0]
        self.assertLess(function.index('InitEventData();'), function.index('Learner_CommitNewGameSettings();'))
        self.assertLess(function.index('RunScriptImmediately(EventScript_ResetAllMapFlags);'), function.index('Learner_CommitNewGameSettings();'))
        intro = (demo.ROOT / 'src/learner_intro.inc').read_text(encoding='utf-8')
        for variable in ('LANGUAGE', 'LEVEL', 'MODE'):
            self.assertIn(f'VarSet(VAR_LEARNER_{variable}', intro)
        self.assertIn('sLearnerSettingsPending = FALSE;', intro)
        clock = (demo.ROOT / 'src/wallclock.c').read_text(encoding='utf-8')
        self.assertIn('LEARNER_UI(VarGet(VAR_LEARNER_LANGUAGE), ClockPrompt)', clock)
        self.assertNotIn('VarSet(VAR_LEARNER_', clock)

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
