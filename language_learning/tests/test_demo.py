"""Run with python -m unittest discover -s language_learning/tests -v."""

import copy
import re
import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
import build_demo as demo
import validate
import opening
import ui
import battle
import field_templates
import graphic_labels


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
                  'data/maps/LittlerootTown_ProfessorBirchsLab/scripts.inc',
                  'data/maps/Route101/scripts.inc', 'data/maps/Route103/scripts.inc', 'data/event_scripts.s']
        paths += [str(path.relative_to(demo.ROOT)) for path in (demo.ROOT / 'data/maps').glob('OldaleTown*/scripts.inc')]
        sources = '\n'.join((demo.ROOT / path).read_text(encoding='utf-8') for path in paths)
        for entry in opening.load()['dialogues']:
            self.assertIn(f"call LearnerOpening_{entry['id']}\n", sources)
            command = 'message' if entry['id'] == 'StarterGift' else 'msgbox'
            self.assertIn(f"\t.else\n\t{command} {entry['base_symbol']}", sources)

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

    def test_town_sign_branches_and_map_buffers_stay_safe(self):
        source = (demo.ROOT / 'data/maps/LittlerootTown/scripts.inc').read_text(encoding='utf-8')
        for sign in ('PlayersHouseSignMale', 'BirchsHouseSignMale'):
            self.assertIn(f'call_if_eq LittlerootTown_EventScript_{sign}\n\t.ifdef LEARNER_DEMO\n\tcheckplayergender', source)
        popup = (demo.ROOT / 'src/map_name_popup.c').read_text(encoding='utf-8')
        self.assertIn('u8 name[20];', popup)
        self.assertIn('Learner_MapName(gMapHeader.regionMapSectionId, name)', popup)
        # Translated names are rendered from ROM, never copied into name[20].
        self.assertNotIn('StringCopy(name, Learner_', popup)

    def test_fixed_ui_and_map_text_are_bounded(self):
        sources = validate.load(demo.ROOT / 'language_learning/ui_sources.json')
        names = validate.load(demo.ROOT / 'language_learning/map_names.json')
        for collection, map_names in ((sources, False), (names, True)):
            for key, entry in collection.items():
                for tag, mapping, glyphs in [('ru', self.russian, self.glyphs), ('de', self.latin, {})]:
                    with self.subTest(key=key, tag=tag):
                        lines = demo.wrap(entry[tag], mapping, glyphs, 96 if map_names else entry['width'])
                        self.assertLessEqual(len(lines), 1 if map_names else entry['lines'])
        self.assertEqual('Wurzelheim', names['MAPSEC_LITTLEROOT_TOWN']['de'])
        self.assertEqual('Вещи', sources['SecretBaseText_ItemStorage']['ru'])

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

    def test_battle_tokens_are_native_and_reject_unknown_controls(self):
        encoded = battle.encode(r'{ATTACKING_MON}:\n{STRING 17}!\p', self.russian, 0)
        self.assertIn(bytes([0xFD, 12]), bytes(encoded))
        self.assertIn(bytes([0xFD, 17]), bytes(encoded))
        self.assertIn(bytes([0xFC, 6, 3, 0xFB, 0xFC, 6, 0]), bytes(encoded))
        with self.assertRaises((KeyError, ValueError)):
            battle.encode('{UNKNOWN_CONTROL}', self.latin, 3)
        with self.assertRaises(ValueError):
            battle.encode('{STRING 255}', self.latin, 3)
        fragment = battle.encode('Angriff', self.latin, 3, fragment=True)
        controlled = battle.encode(
            '{PLAY_SE SE_FLEE}{POKEBLOCK}{PLAY_BGM MUS_CAUGHT}', self.latin, 3)
        self.assertIn(bytes([0xFC, 0x10, 0x11, 0]), bytes(controlled))
        self.assertIn(bytes([0x55, 0x56, 0x57, 0x58, 0x59]), bytes(controlled))
        self.assertIn(bytes([0xFC, 0x0B, 0x60, 1]), bytes(controlled))
        with self.assertRaises(ValueError):
            battle.validate_line_width('x' * 26, {})
        self.assertNotIn(0xFC, fragment)
        self.assertEqual(0xFF, fragment[-1])

    def test_field_move_forgetting_keeps_timing_sound_and_runtime_names(self):
        entries = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        entry = entries['gOtherText_ForgetMove123_2']
        self.assertEqual({'STR_VAR_1': 10, 'STR_VAR_2': 12}, entry['buffer_lengths'])
        for tag, mapping, glyphs, font in (
                ('ru', self.russian, self.glyphs, 0),
                ('de', self.latin, {}, 3)):
            data = field_templates.compile_text(
                entry[tag], mapping, glyphs, font, entry['widths'],
                entry['max_width'], entry['buffer_lengths'])
            self.assertIn(bytes([0xFC, 8, 32]), bytes(data))
            self.assertEqual(5, bytes(data).count(bytes([0xFC, 8, 15])))
            self.assertIn(bytes([0xFC, 16, 56, 0]), bytes(data))
            self.assertIn(bytes([0xFD, 2]), bytes(data))
            self.assertIn(bytes([0xFD, 3]), bytes(data))
        with self.assertRaises(ValueError):
            field_templates.compile_text('{PAUSE 256}', self.latin, {}, 3, {})
        with self.assertRaises(KeyError):
            field_templates.compile_text('{PLAY_SE UNKNOWN}', self.latin, {}, 3, {})

    def test_money_sprite_is_localized_and_keeps_native_size(self):
        labels = validate.load(demo.ROOT / 'language_learning/graphic_labels.json')
        self.assertEqual('ДЕНЬГИ', labels['money'][0]['ru'])
        self.assertEqual('GELD', labels['money'][0]['de'])
        for tag in ('ru', 'de'):
            rendered = graphic_labels.render('money', tag)
            self.assertEqual((32, 16), rendered.size)
            self.assertEqual(256, len(graphic_labels.tile_bytes(rendered)))
        source = (demo.ROOT / 'src/money.c').read_text(encoding='utf-8')
        self.assertIn('gLearnerMoneyTilesRu : gLearnerMoneyTilesDe', source)
        self.assertIn('LoadCompressedObjectPic(&learnerMoneySheet);', source)

    def test_phase_three_shared_screens_have_no_unclassified_text_symbols(self):
        known = set()
        for path in ('ui_sources.json', 'field_templates.json', 'ui.json'):
            known.update(validate.load(demo.ROOT / 'language_learning' / path))
        phase_sources = (
            'item_menu.c', 'item_use.c', 'pokedex.c', 'start_menu.c',
            'save_menu_util.c', 'party_menu.c', 'pokemon_summary_screen.c',
            'pokemon_storage_system.c', 'shop.c',
        )
        pattern = re.compile(
            r'\b(?:g(?:OtherText|SystemText|DexText|PCText|Text)_[A-Za-z0-9_]+'
            r'|OtherText_[A-Za-z0-9_]+|SystemText_[A-Za-z0-9_]+'
            r'|PCText_[A-Za-z0-9_]+)\b')
        referenced = set()
        for name in phase_sources:
            referenced.update(pattern.findall(
                (demo.ROOT / 'src' / name).read_text(encoding='utf-8')))
        nonlanguage = {
            'gOtherText_CancelWithTerminator', 'gOtherText_Comma',
            'gOtherText_FemaleSymbol2', 'gOtherText_FiveQuestions',
            'gOtherText_MaleSymbol2', 'gOtherText_OneDash',
            'gOtherText_TallPlusAndRightArrow', 'gOtherText_Terminator18',
            'gOtherText_ThreeDashes2', 'gOtherText_TwoDashes',
            'gOtherText_xString1', 'SystemText_Player',
        }
        self.assertEqual(nonlanguage, referenced - known)

    def test_battle_sources_names_and_font_restore(self):
        parts, table = battle.generate(self.russian, self.latin)
        self.assertTrue(parts)
        self.assertTrue(any('gMoveNames + 13 * MOVE_SCRATCH' in row for row in table))
        names = validate.load(demo.ROOT / 'language_learning/battle_names.json')
        moves = {key for key in names if key.startswith('MOVE_')}
        move_constants = set(re.findall(
            r'^#define (MOVE_[A-Z0-9_]+) \d+$',
            (demo.ROOT / 'include/constants/moves.h').read_text(encoding='utf-8'),
            re.MULTILINE))
        move_constants.remove('MOVE_NONE')
        self.assertEqual(move_constants, moves)
        self.assertEqual(names['MOVE_FOCUS_PUNCH']['de'], 'Power-P.')
        for move in ('MOVE_CUT', 'MOVE_FLY', 'MOVE_HEADBUTT', 'MOVE_DISABLE',
                     'MOVE_SURF', 'MOVE_ICE_BEAM', 'MOVE_EARTHQUAKE',
                     'MOVE_PSYCHIC', 'MOVE_HYPNOSIS', 'MOVE_RECOVER',
                     'MOVE_LIGHT_SCREEN', 'MOVE_SELF_DESTRUCT',
                     'MOVE_DREAM_EATER', 'MOVE_TRANSFORM', 'MOVE_REST',
                     'MOVE_SUBSTITUTE', 'MOVE_AEROBLAST', 'MOVE_PROTECT',
                     'MOVE_SPIKES', 'MOVE_SANDSTORM', 'MOVE_BATON_PASS',
                     'MOVE_IRON_TAIL', 'MOVE_RAIN_DANCE', 'MOVE_SHADOW_BALL',
                     'MOVE_HELPING_HAND', 'MOVE_SUPERPOWER', 'MOVE_DIVE',
                     'MOVE_BLAZE_KICK', 'MOVE_METEOR_MASH',
                     'MOVE_WEATHER_BALL', 'MOVE_CALM_MIND',
                     'MOVE_PSYCHO_BOOST'):
            self.assertIn(move, moves)
            self.assertTrue(any(f'gMoveNames + 13 * {move}' in row for row in table))
        code = (demo.ROOT / 'src/battle_message.c').read_text(encoding='utf-8')
        self.assertIn('src = LEARNER_BATTLE(src);', code)
        self.assertIn('toCpy = LEARNER_BATTLE(toCpy);', code)
        self.assertIn('dst[dstID++] = Learner_GetLanguage() == 1 ? 0 : 3;', code)
        # Never place longer translated names into the engine's 16-byte buffers.
        self.assertNotIn('StringCopy(gBattleTextBuff2, LEARNER_BATTLE', code)
        entries = validate.load(demo.ROOT / 'language_learning/battle.json')
        for tag in ('ru', 'de'):
            self.assertIn('{STRING 17}', entries['BattleText_OpponentUsedMove'][tag])

    def test_extended_shared_battle_flows_are_bilingual(self):
        entries = validate.load(demo.ROOT / 'language_learning/battle.json')
        self.assertGreaterEqual(len(entries), 456)
        expected = (
            'BattleText_WildDoubleAppeared', 'BattleText_DoubleWantToBattle',
            'BattleText_SentOutDouble1', 'BattleText_WithdrewPoke1',
            'BattleText_GiveNickname', 'BattleText_SentToPC',
            'BattleText_AddedToDex', 'BattleText_CuredParalysis',
            'BattleText_RestoredHealth', 'BattleText_StartEvo',
            'BattleText_FinishEvo', 'BattleText_StopEvo',
            'BattleText_AvoidedAttack', 'BattleText_BecameConfused',
            'BattleText_BadlyPoisoned', 'BattleText_FrozenSolid',
            'BattleText_NoMovesLeft', 'BattleText_NoPP1',
            'BattleText_MustRecharge', 'BattleText_Paralyzed2',
            'BattleText_RestoredHPByItem', 'BattleText_AlreadyPoisoned',
            'BattleText_MoveIsDisabled', 'BattleText_HitRecoil',
            'BattleText_ProtectedItself', 'BattleText_SafeguardFaded',
            'BattleText_SandBuffeted', 'BattleText_SunIntensified',
            'BattleText_HailStricken', 'BattleText_SpikesScattered',
            'BattleText_PreventedBurn', 'BattleText_PreventedBy',
            'BattleText_UproarCantSleep', 'BattleText_SandTombTrapped',
            'BattleText_GotFreeFrom', 'BattleText_CurseLay',
            'BattleText_PerishSongFell', 'BattleText_SubTookDamage',
            'BattleText_RaisedDefense', 'BattleText_CopyStatChanges',
            'BattleText_MadeType', 'BattleText_Transformed',
            'BattleText_TookAim', 'BattleText_NaturePower',
            'BattleText_StockpiledCant', 'BattleText_HealthSapped',
            'BattleText_TryingToLearnMove', 'BattleText_DeleteMove',
            'BattleText_GroundMoveNegate', 'BattleText_MadeAsleep',
            'BattleText_StoppedWorking', 'BattleText_FlewHigh',
            'BattleText_WoreOff', 'BattleText_FatigueConfuse',
            'BattleText_PickedUpYen', 'BattleText_DestinyBondTaken',
            'BattleText_SwitchedItems', 'BattleText_GrudgeLosePP',
            'BattleText_MagicCoatBounce', 'BattleText_CantUseItems',
            'BattleText_TauntNoUse', 'BattleText_BlocksOther2',
            'BattleText_MoveForget123', 'BattleText_SafariOver',
            'BattleText_BallCaught1', 'BattleText_MenuOptionsSafari',
            'BattleText_ForgetMove', 'BattleText_SafariBalls',
            'BattleText_Win', 'BattleText_Dark',
        )
        for symbol in expected:
            self.assertEqual({'ru', 'de'}, set(entries[symbol]))
        for tag, mapping, font in (('ru', self.russian, 0), ('de', self.latin, 3)):
            fled = battle.encode(entries['BattleText_FledSingle'][tag], mapping, font)
            self.assertIn(bytes(battle.TOKENS['FLEE']), bytes(fled))
            caught = battle.encode(entries['BattleText_AddedToDex'][tag], mapping, font)
            self.assertIn(bytes([0xFD, 3]), bytes(caught))

    def test_battle_catalogue_only_omits_control_and_composition_fragments(self):
        source = (demo.ROOT / 'src/data/battle_strings_en.h').read_text(encoding='utf-8')
        symbols = set(re.findall(r'const u8 (Battle(?:Stat)?Text_\w+)\[\]', source))
        translated = set(validate.load(demo.ROOT / 'language_learning/battle.json'))
        internal = {
            'BattleText_UnknownString', 'BattleText_Terminator',
            'BattleText_Terminator2', 'BattleText_Exclamation',
            'BattleText_Exclamation2', 'BattleText_Exclamation3',
            'BattleText_Exclamation4', 'BattleText_Exclamation5',
            'BattleText_Format', 'BattleText_Format2',
            'BattleText_RightArrow', 'BattleText_Plus', 'BattleText_Dash',
            'BattleText_HighlightRed', 'BattleText_Format3',
            'BattleText_Format4', 'BattleText_Format5', 'BattleText_Format6',
            'BattleText_Format7', 'BattleText_Format8', 'BattleText_Format9',
            'BattleText_Format10', 'BattleText_Format11',
        }
        self.assertEqual(internal, symbols - translated)

    def test_briefcase_nickname_and_pause_labels_are_registered(self):
        entries = validate.load(demo.ROOT / 'language_learning/ui_sources.json')
        for name in ('OtherText_PokeName', 'gOtherText_BirchInTrouble', 'SystemText_Save', 'SystemText_BAG'):
            self.assertEqual({'ru', 'de', 'width', 'lines'}, set(entries[name]))
        self.assertLessEqual(entries['SystemText_Save']['width'], 56)

    def test_storage_and_pokedex_detail_labels_are_registered(self):
        entries = validate.load(demo.ROOT / 'language_learning/ui_sources.json')
        storage = (
            'PCText_ExitBox', 'PCText_WhatYouDo', 'PCText_ReleasePoke',
            'PCText_Deposit', 'PCText_Withdraw', 'PCText_Move',
            'PCText_Summary', 'PCText_Mark', 'PCText_Name',
            'PCText_Jump', 'PCText_Wallpaper', 'PCText_Cancel2',
        )
        for name in storage + ('gDexText_CryOf', 'gDexText_SizeComparedTo'):
            self.assertEqual({'ru', 'de', 'width', 'lines'}, set(entries[name]))
        for name in storage[3:]:
            self.assertEqual(1, entries[name]['lines'])

    def test_party_and_summary_shared_text_use_learner_translations(self):
        entries = validate.load(demo.ROOT / 'language_learning/ui_sources.json')
        party = (demo.ROOT / 'src/party_menu.c').read_text(encoding='utf-8')
        summary = (demo.ROOT / 'src/pokemon_summary_screen.c').read_text(encoding='utf-8')
        self.assertIn('PartyLearnerText(PartyMenuPromptTexts[textId])', party)
        self.assertIn('MenuPrintMessage(PartyLearnerText(message)', party)
        self.assertIn('src = SummaryLearnerText(src);', summary)
        self.assertEqual(2, summary.count('SummaryLearnerText(sPageHeaderTexts['))
        self.assertEqual(1, summary.count('SummaryCopyEnigmaItemName(itemId, gStringVar1);'))
        self.assertEqual(1, summary.count('SummaryCopyItemName(itemId, gStringVar1);'))
        self.assertIn(
            '#define SummaryCopyEnigmaItemName(itemId, dest) '
            'StringCopy(dest, ItemId_GetName(itemId))',
            summary,
        )
        self.assertIn('#define SummaryCopyItemName CopyItemName', summary)
        self.assertEqual(3, summary.count('SummaryLearnerText(gMoveNames[move])'))
        self.assertEqual(25, summary.count('case NATURE_'))
        self.assertEqual(154, summary.count('case ABILITY_'))
        self.assertEqual(3, summary.count('SummaryMapName(locationMet, gStringVar1)'))
        pokemon_menu = (demo.ROOT / 'src/pokemon_menu.c').read_text(encoding='utf-8')
        self.assertIn('Learner_Translate(menuActions[order[i]].text)', pokemon_menu)
        self.assertNotIn('StringCopy(gStringVar2, gMoveNames[', party)
        for name in ('OtherText_ChoosePoke', 'OtherText_RestoreWhatMove',
                     'OtherText_PokeInfo', 'OtherText_PokeSkills',
                     'gOtherText_Attack', 'gOtherText_Defense',
                     'gOtherText_ExpPoints', 'gOtherText_NextLv',
                     'OtherText_Summary', 'OtherText_Item', 'OtherText_Mail',
                     'gOtherText_Nature', 'gOtherText_Met',
                     'gOtherText_EggObtainedInTrade'):
            self.assertIn(name, entries)
        for name in ('gOtherText_EggLongTime', 'gOtherText_EggSomeTime',
                     'gOtherText_EggSoon', 'gOtherText_EggAbout'):
            self.assertIn(name, entries)
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        self.assertEqual({'ru', 'de', 'widths', 'max_width'}, set(templates['OtherText_DoWhat']))
        for name in ('gOtherText_WasGivenToHold', 'gOtherText_AlreadyHolding',
                     'gOtherText_LearnedMove', 'gOtherText_WantsToLearn',
                     'gOtherText_HPRestoredBy', 'gOtherText_WasRaised',
                     'gOtherText_ThatWillBe2', 'gOtherText_SpaceForIsFull'):
            self.assertIn(name, templates)
        ui_entries = validate.load(demo.ROOT / 'language_learning/ui.json')
        abilities = [name for name in ui_entries
                     if name.startswith('Ability') and not name.endswith('Desc')]
        self.assertEqual(77, len(abilities))
        for name in abilities:
            for tag, mapping, glyphs in [('ru', self.russian, self.glyphs),
                                         ('de', self.latin, {})]:
                self.assertEqual(1, len(demo.wrap(ui_entries[name][tag], mapping, glyphs, 136)))

    def test_options_save_and_bag_paths_use_learner_translations(self):
        entries = validate.load(demo.ROOT / 'language_learning/ui_sources.json')
        option = (demo.ROOT / 'src/option_menu.c').read_text(encoding='utf-8')
        self.assertIn(
            '#if LEARNER_DEMO\nstatic u8 sLearnerOptionChoiceText[7][32];',
            option,
        )
        save = (demo.ROOT / 'src/save_menu_util.c').read_text(encoding='utf-8')
        bag = (demo.ROOT / 'src/item_menu.c').read_text(encoding='utf-8')
        option_symbols = (
            'gSystemText_OptionMenu', 'gSystemText_TextSpeed',
            'gSystemText_BattleScene', 'gSystemText_BattleStyle',
            'gSystemText_Sound', 'gSystemText_ButtonMode',
            'gSystemText_Frame', 'gSystemText_Cancel',
            'gSystemText_Slow', 'gSystemText_Mid', 'gSystemText_Fast',
            'gSystemText_On', 'gSystemText_Off', 'gSystemText_Shift',
            'gSystemText_Set', 'gSystemText_Mono', 'gSystemText_Stereo',
            'gSystemText_Type', 'gSystemText_Normal',
            'gSystemText_LR', 'gSystemText_LA',
        )
        for symbol in option_symbols:
            self.assertIn(symbol, entries)
            self.assertIn(f'OptionLearnerText({symbol})', option)
        for symbol in ('gOtherText_Player', 'gOtherText_Badges',
                       'gOtherText_Pokedex', 'gOtherText_PlayTime'):
            self.assertIn(f'SaveLearnerText({symbol})', save)
        for symbol in ('gOtherText_Walk', 'gOtherText_Check',
                       'gOtherText_BootedTM', 'gOtherText_BootedHM'):
            self.assertIn(symbol, entries)
        for symbol in ('gSystemText_SaveErrorExchangeBackup', 'gSystemText_Saving',
                       'gDexText_UnknownPoke', 'gDexText_UnknownHeight',
                       'gDexText_UnknownWeight'):
            self.assertIn(symbol, entries)
        self.assertGreaterEqual(bag.count('BagLearnerText(sItemPopupMenuActions['), 4)
        self.assertGreaterEqual(bag.count('Menu_PrintText(BagLearnerText(text)'), 2)

    def test_early_pokedex_entries_are_bilingual_and_fit(self):
        entries = validate.load(demo.ROOT / 'language_learning/ui.json')
        species = tuple(sorted(name[:-10] for name in entries if name.endswith('DexPageOne')))
        self.assertGreaterEqual(len(species), 74)
        for name in species:
            for suffix in ('Name', 'Kind', 'DexPageOne', 'DexPageTwo'):
                self.assertEqual({'ru', 'de'}, set(entries[name + suffix]))
            self.assertLessEqual(len(demo.encode(entries[name + 'Name']['ru'], self.russian)), 10)
            self.assertLessEqual(len(demo.encode(entries[name + 'Name']['de'], self.latin)), 10)
            for page in ('DexPageOne', 'DexPageTwo'):
                for tag, mapping, glyphs in [('ru', self.russian, self.glyphs), ('de', self.latin, {})]:
                    self.assertLessEqual(len(demo.wrap(entries[name + page][tag], mapping, glyphs, 152)), 3)
        code = (demo.ROOT / 'src/pokedex.c').read_text()
        for name in species:
            self.assertIn('NATIONAL_DEX_' + name.upper(), code)
            self.assertIn(name + 'DexPageOne', code)
            self.assertIn(name + 'DexPageTwo', code)

    def test_pokedex_categories_fit_with_pokemon_suffix(self):
        entries = validate.load(demo.ROOT / 'language_learning/ui.json')
        species = tuple(name[:-4] for name in entries if name.endswith('Kind'))
        self.assertGreaterEqual(len(species), 104)
        code = (demo.ROOT / 'src/pokedex.c').read_text()
        for name in species:
            self.assertEqual({'ru', 'de'}, set(entries[name + 'Name']))
            self.assertIn('NATIONAL_DEX_' + name.upper(), code)
            self.assertIn(name + 'Name', code)
            self.assertIn(name + 'Kind', code)
            for tag, mapping, glyphs in [('ru', self.russian, self.glyphs), ('de', self.latin, {})]:
                self.assertLessEqual(len(demo.encode(entries[name + 'Name'][tag], mapping)), 10)
                self.assertLessEqual(len(demo.encode(entries[name + 'Kind'][tag], mapping)), 16)
                category = entries[name + 'Kind'][tag] + ' POKéMON'
                self.assertEqual(len(demo.wrap(category, mapping, glyphs, 152)), 1)

    def test_every_hoenn_dex_species_is_translated(self):
        import re
        entries = validate.load(demo.ROOT / 'language_learning/ui.json')
        constants = (demo.ROOT / 'include/constants/species.h').read_text()
        species = [name.title().replace('_', '') for name, number in
                   re.findall(r'^#define HOENN_DEX_([A-Z0-9_]+)\s+(\d+)', constants, re.M)
                   if 0 < int(number) <= 202]
        self.assertEqual(202, len(species))
        for name in species:
            for suffix in ('Name', 'Kind', 'DexPageOne', 'DexPageTwo'):
                self.assertIn(name + suffix, entries)

    def test_pokedex_descriptions_are_complete_and_distinct(self):
        entries = validate.load(demo.ROOT / 'language_learning/ui.json')
        for tag in ('ru', 'de'):
            descriptions = [value[tag] for key, value in entries.items()
                            if key.endswith(('DexPageOne', 'DexPageTwo'))]
            self.assertEqual(404, len(descriptions))
            self.assertEqual(404, len(set(descriptions)))
            for description in descriptions:
                self.assertTrue(description.endswith(('.', '!', '?')), description)
                self.assertEqual(description.strip(), description)
                self.assertNotIn('  ', description)

    def test_oldale_dialogues_cover_all_local_text(self):
        import re
        entries = {entry['base_symbol'] for entry in opening.load()['dialogues']}
        for path in (demo.ROOT / 'data/maps').glob('OldaleTown*/text.inc'):
            symbols = re.findall(r'^(OldaleTown\w*Text_\w+)::', path.read_text(encoding='utf-8'), re.M)
            self.assertTrue(set(symbols) <= entries, path.name)
        # Service scripts keep their native result/animation/transaction flow.
        nurse = (demo.ROOT / 'data/scripts/pkmn_center_nurse.inc').read_text()
        self.assertIn('msgbox gText_NurseJoy_Welcome, MSGBOX_YESNO', nurse)
        town = (demo.ROOT / 'data/maps/OldaleTown/scripts.inc').read_text()
        self.assertIn('giveitem ITEM_POTION\n\tcompare VAR_RESULT, 0', town)

    def test_shop_confirmation_keeps_quantity_and_price(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        for tag, mapping, glyphs, font in [('ru', self.russian, self.glyphs, 0), ('de', self.latin, {}, 3)]:
            entry = templates['gOtherText_ThatWillBe']
            encoded = bytes(field_templates.compile_text(entry[tag], mapping, glyphs, font, entry['widths']))
            for token in (2, 3, 4):
                self.assertIn(bytes([0xFD, token, 0xFC, 6, font]), encoded)
            self.assertIn(0xFE, encoded)
        with self.assertRaises((KeyError, ValueError)):
            field_templates.compile_text('{PLAYER}', self.latin, {}, 3, {})
        with self.assertRaises(ValueError):
            field_templates.compile_text('{STR_VAR_1}', self.latin, {}, 3, {'STR_VAR_1': 300})

    def test_shop_text_does_not_change_global_item_buffers(self):
        code = (demo.ROOT / 'src/shop.c').read_text(encoding='utf-8')
        self.assertIn('#define Learner_CopyItemName CopyItemName', code)
        item = (demo.ROOT / 'src/item.c').read_text(encoding='utf-8')
        self.assertIn('#if LEARNER_DEMO\n    const u8 *translated = Learner_ItemText', item)
        self.assertNotRegex(item, r'gItems\[[^]]+\]\.name\s*=')
        self.assertNotRegex(item, r'gItems\[[^]]+\]\.description\s*=')
        entries = validate.load(demo.ROOT / 'language_learning/ui.json')
        for key in ('Potion', 'Antidote', 'ParaHeal', 'Awakening', 'PokeBall'):
            for tag, mapping, glyphs in [('ru', self.russian, self.glyphs), ('de', self.latin, {})]:
                self.assertEqual(1, len(demo.wrap(entries[key][tag], mapping, glyphs, 88)))

    def test_shared_item_messages_preserve_runtime_fields(self):
        entries = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        expected = {'Text_ObtainedTheItem': [3], 'Text_FoundOneItem': [1, 3],
                    'Text_PutItemInPocket': [3, 4], 'gOtherText_SoldItem': [2, 3],
                    'gOtherText_WithdrewThing': [2, 3],
                    'gOtherText_HowManyYouWant': [2],
                    'gOtherText_WhatWillYouDoMail': [2],
                    'gPCText_PlayersPC': [1],
                    'gSecretBaseText_NoMoreDecor': [2],
                    'gSecretBaseText_NoMoreDecor2': [2],
                    'gSecretBaseText_WillBeDiscarded': [2],
                    'gOtherText_Coins3': [2], 'gOtherText_ContainsMove': [2],
                    'gOtherText_SnapConfusion': [2], 'gOtherText_SafariStock': [2]}
        exports = (demo.ROOT / 'data/text/obtain_item.inc').read_text()
        pc_source = (demo.ROOT / 'src/player_pc.c').read_text(encoding='utf-8')
        response = pc_source.split('static void ItemStorage_PrintItemPcResponse(u16 itemId)\n{', 1)[1].split('\n}', 1)[0]
        self.assertIn('string = Learner_Translate(string);', response)
        self.assertIn('string = ItemId_GetDescription(itemId);', response)
        self.assertIn('StringExpandPlaceholders(gStringVar4, gOtherText_WhatWillYouDoMail)', pc_source)
        shop_source = (demo.ROOT / 'src/shop.c').read_text(encoding='utf-8')
        self.assertIn('StringExpandPlaceholders(gStringVar4, gOtherText_HowManyYouWant)', shop_source)
        expansion_source = (demo.ROOT / 'src/string_util.c').read_text(encoding='utf-8')
        self.assertIn('src = Learner_Translate(src);', expansion_source)
        menu_source = (demo.ROOT / 'src/script_menu.c').read_text(encoding='utf-8')
        self.assertIn('Menu_PrintText(PC_MENU_TEXT(gPCText_PlayersPC)', menu_source)
        decor_source = (demo.ROOT / 'src/decoration.c').read_text(encoding='utf-8')
        for symbol in ('gSecretBaseText_NoMoreDecor', 'gSecretBaseText_NoMoreDecor2',
                       'gSecretBaseText_WillBeDiscarded'):
            self.assertIn(f'StringExpandPlaceholders(gStringVar4, {symbol})', decor_source)
        fixed_sources = validate.load(demo.ROOT / 'language_learning/ui_sources.json')
        self.assertFalse(set(expected) & set(fixed_sources))
        original_strings = (demo.ROOT / 'src/strings.c').read_text(encoding='utf-8')
        for symbol in fixed_sources:
            source = re.search(r'const u8 ' + re.escape(symbol) + r'\[\] = _\((.*?)\);',
                               original_strings, re.DOTALL)
            if source:
                self.assertNotRegex(source.group(1), r'\{(?:PLAYER|STR_VAR_[123])\}',
                                    f'{symbol} loses a live value in its fixed translation')
        for symbol, tokens in expected.items():
            entry = entries[symbol]
            if symbol.startswith('Text_'):
                self.assertIn(symbol + '::', exports)
            for tag, mapping, glyphs, font in [('ru', self.russian, self.glyphs, 0), ('de', self.latin, {}, 3)]:
                data = bytes(field_templates.compile_text(entry[tag], mapping, glyphs, font, entry['widths']))
                for token in tokens:
                    self.assertIn(bytes([0xFD, token, 0xFC, 6, font]), data)
        with self.assertRaises(ValueError):
            field_templates.compile_text('{STR_VAR_1}\\p{STR_VAR_1}\\p{STR_VAR_1}', self.latin, {}, 3, {'STR_VAR_1': 80})

    def test_graphic_labels_preserve_tiles_and_borders(self):
        from PIL import Image
        entries = validate.load(demo.ROOT / 'language_learning/graphic_labels.json')
        for kind, (path, _, size) in graphic_labels.SHEETS.items():
            with Image.open(demo.ROOT / path) as original:
                source = original.copy()
            if kind in ('storage_misc', 'summary'):
                source = source.point(lambda value: 15 - value // 17).convert('P')
            for tag in ('ru', 'de'):
                rendered = graphic_labels.render(kind, tag)
                packed = graphic_labels.tile_bytes(rendered)
                self.assertEqual(len(packed), size[0] * size[1] // 2)
                allowed = set()
                for e in entries[kind]:
                    x, y = e['x'], e['y']
                    if 'bottom_x' in e:
                        allowed.update((px, py) for px in range(x, x + 24) for py in range(y, y + 8))
                        allowed.update((px, py) for px in range(e['bottom_x'], e['bottom_x'] + 24) for py in range(y + 8, y + 16))
                        continue
                    elif kind == 'bag':
                        rect = (x, y + 1, x + 64, y + 15)
                    elif kind == 'dex_search':
                        rect = (x + 5, y + 2, x + 36, y + 14)
                    elif kind == 'summary':
                        rect = (x, y, x + e['width'], y + 8)
                    else:
                        rect = (x, y, x + e['width'], y + e.get('height', 16))
                    allowed.update((px, py) for px in range(rect[0], rect[2]) for py in range(rect[1], rect[3]))
                for y in range(size[1]):
                    for x in range(size[0]):
                        if (x, y) not in allowed:
                            self.assertEqual(source.getpixel((x, y)), rendered.getpixel((x, y)))
                        offset = ((y // 8) * (size[0] // 8) + x // 8) * 32 + (y % 8) * 4 + (x % 8) // 2
                        self.assertEqual(rendered.getpixel((x, y)), (packed[offset] >> (4 * (x % 2))) & 15)

    def test_type_icon_labels_keep_sprite_layout_and_borders(self):
        from PIL import Image
        entries = validate.load(demo.ROOT / 'language_learning/graphic_labels.json')['type_icons']
        self.assertEqual(graphic_labels.TYPE_ICON_NAMES,
                         tuple(entry['name'] for entry in entries))
        for tag in ('ru', 'de'):
            sheet = graphic_labels.render_type_icons(tag)
            self.assertEqual((32, 16 * 23), sheet.size)
            self.assertEqual(23 * 0x100, len(graphic_labels.tile_bytes(sheet)))
            for index, entry in enumerate(entries):
                with Image.open(demo.ROOT / f'graphics/types/{entry["name"]}.png') as source:
                    icon = source.copy()
                result = sheet.crop((0, index * 16, 32, (index + 1) * 16))
                for x in range(32):
                    self.assertEqual(icon.getpixel((x, 0)), result.getpixel((x, 0)))
                    self.assertEqual(icon.getpixel((x, 15)), result.getpixel((x, 15)))
                for y in range(16):
                    self.assertEqual(icon.getpixel((0, y)), result.getpixel((0, y)))
                    self.assertEqual(icon.getpixel((31, y)), result.getpixel((31, y)))
                if entry['name'] == 'mystery':
                    self.assertEqual(icon.tobytes(), result.tobytes())
            with Image.open(demo.ROOT / 'graphics/types/fire.png') as source:
                self.assertNotEqual(source.tobytes(), sheet.crop((0, 160, 32, 176)).tobytes())
        summary = (demo.ROOT / 'src/pokemon_summary_screen.c').read_text()
        self.assertIn('gLearnerMoveTypeTilesRu : gLearnerMoveTypeTilesDe', summary)
        self.assertIn('LoadCompressedObjectPic(&sSpriteSheet_MoveTypes);', summary)

    def test_status_icon_labels_keep_party_and_summary_layout(self):
        from PIL import Image
        entries = validate.load(demo.ROOT / 'language_learning/graphic_labels.json')['status_icons']
        self.assertEqual(graphic_labels.STATUS_ICON_NAMES,
                         tuple(entry['name'] for entry in entries))
        with Image.open(demo.ROOT / 'graphics/interface/status_icons.png') as source:
            original = source.copy()
        self.assertEqual(bytes(graphic_labels.tile_bytes(original)),
                         (demo.ROOT / 'graphics/interface/status_icons.4bpp').read_bytes())
        for tag in ('ru', 'de'):
            sheet = graphic_labels.render_status_icons(tag)
            self.assertEqual((32, 56), sheet.size)
            self.assertEqual(0x380, len(graphic_labels.tile_bytes(sheet)))
            self.assertNotEqual(original.tobytes(), sheet.tobytes())
            for index in range(len(entries)):
                self.assertIn(2, [sheet.getpixel((x, y)) for y in range(index * 8 + 1, index * 8 + 7)
                                  for x in range(8, 24)])
            for y in range(56):
                for x in range(32):
                    if not (8 <= x < 24 and y % 8 in range(1, 7)):
                        self.assertEqual(original.getpixel((x, y)), sheet.getpixel((x, y)))
        party = (demo.ROOT / 'src/party_menu.c').read_text(encoding='utf-8')
        summary = (demo.ROOT / 'src/pokemon_summary_screen.c').read_text(encoding='utf-8')
        self.assertIn('gLearnerStatusIconTilesRu', party)
        self.assertIn('gLearnerStatusIconTilesRu', summary)
        self.assertIn('LZDecompressVram(gStatusGfx_Icons', party)
        self.assertIn('LoadCompressedObjectPic(&sUnknown_083C12F4);', summary)

    def test_battle_status_icons_replace_only_five_healthbox_badges(self):
        from PIL import Image
        base = demo.ROOT / 'graphics/battle_interface'
        originals = []
        for name in graphic_labels.BATTLE_STATUS_FILES:
            with Image.open(base / f'status_{name}.png') as source:
                originals.append(source.copy())
        combined = (base / 'healthbox_elements.4bpp').read_bytes()
        self.assertEqual(combined[0x15 * 32:0x24 * 32],
                         b''.join((base / f'status_{name}.4bpp').read_bytes()
                                  for name in graphic_labels.BATTLE_STATUS_FILES))
        for tag in ('ru', 'de'):
            sheet = graphic_labels.render_battle_status_icons(tag)
            self.assertEqual((24, 40), sheet.size)
            self.assertEqual(15 * 32, len(graphic_labels.tile_bytes(sheet)))
            for index, original in enumerate(originals):
                icon = sheet.crop((0, index * 8, 24, (index + 1) * 8))
                self.assertNotEqual(original.tobytes(), icon.tobytes())
                self.assertIn(2, [icon.getpixel((x, y)) for y in range(1, 7)
                                  for x in range(3, 18)])
                for y in range(8):
                    for x in range(24):
                        if not (3 <= x < 18 and 1 <= y < 7):
                            self.assertEqual(original.getpixel((x, y)), icon.getpixel((x, y)))
        battle = (demo.ROOT / 'src/battle_interface.c').read_text(encoding='utf-8')
        self.assertIn('gLearnerBattleStatusTilesRu', battle)
        self.assertIn('sStatusTileStarts[] = {0x15, 0x47, 0x56, 0x65}', battle)
        self.assertIn('a < sStatusTileStarts[i] + 15', battle)
        self.assertIn('a - sStatusTileStarts[i]', battle)
        self.assertIn('return gHealthboxElementsGfxTable[a];', battle)

    def test_area_unknown_sign_keeps_its_three_sprite_borders(self):
        from PIL import Image
        with Image.open(demo.ROOT / 'graphics/pokedex/area_unknown.png') as source:
            original = source.copy()
        for tag in ('ru', 'de'):
            rendered = graphic_labels.render_area_unknown(tag)
            self.assertEqual((32, 96), rendered.size)
            self.assertEqual(0x600, len(graphic_labels.tile_bytes(rendered)))
            self.assertNotEqual(original.tobytes(), rendered.tobytes())
            for frame in range(3):
                for y in range(32):
                    for x in range(32):
                        combined_x = x + frame * 32
                        if not (8 <= combined_x < 88 and 7 <= y < 25):
                            self.assertEqual(original.getpixel((x, y + frame * 32)),
                                             rendered.getpixel((x, y + frame * 32)))
        area = (demo.ROOT / 'src/pokedex_area_screen.c').read_text()
        self.assertIn('gLearnerAreaUnknownTilesRu', area)
        self.assertIn('LZ77UnCompWram(tiles', area)

    def test_pokedex_size_caption_uses_the_selected_language(self):
        pokedex = (demo.ROOT / 'src/pokedex.c').read_text()
        self.assertIn('StringAppend(string, DexLearnerText(gDexText_SizeComparedTo));', pokedex)

    def test_shared_item_names_and_descriptions_fit(self):
        item_source = (demo.ROOT / 'src/item.c').read_text()
        for signature in ('void CopyItemName(', 'const u8 *ItemId_GetName(',
                          'const u8 *ItemId_GetDescription('):
            body = item_source.split(signature, 1)[1].split('\n}', 1)[0]
            self.assertIn('Learner_ItemText(itemId,', body)
        self.assertIn('const u8 *description = ItemId_GetDescription(itemId);', item_source)
        code = (demo.ROOT / 'src/shop.c').read_text()
        self.assertIn('gLearnerItemTranslations[low].itemId == itemId', code)
        self.assertIn('gLearnerItemTranslations[low].descriptions[language]', code)
        entries = validate.load(demo.ROOT / 'language_learning/items.json')
        machines = ui.machine_items()
        self.assertEqual(len(machines), 58)
        self.assertFalse(set(entries) & set(machines))
        self.assertEqual(machines['ITEM_TM01_FOCUS_PUNCH']['de']['name'], 'TM01')
        self.assertEqual(machines['ITEM_TM22_SOLARBEAM']['ru']['name'], 'TM22')
        self.assertEqual(machines['ITEM_HM08_DIVE']['de']['name'], 'HM08')
        assembly = '\n'.join(ui.generate(self.russian, self.latin, self.glyphs))
        self.assertIn('gLearnerItemTranslations::', assembly)
        self.assertIn(f'gLearnerItemTranslationCount::\n\t.2byte {len(entries) + len(machines)}', assembly)
        table_items = re.findall(r'^\t\.2byte (ITEM_[A-Z0-9_]+), 0$', assembly, re.MULTILINE)
        self.assertEqual(set(table_items), set(entries) | set(machines))
        self.assertGreaterEqual(len(entries), 165)
        balls = {
            'ITEM_MASTER_BALL', 'ITEM_ULTRA_BALL', 'ITEM_GREAT_BALL',
            'ITEM_POKE_BALL', 'ITEM_SAFARI_BALL', 'ITEM_NET_BALL',
            'ITEM_DIVE_BALL', 'ITEM_NEST_BALL', 'ITEM_REPEAT_BALL',
            'ITEM_TIMER_BALL', 'ITEM_LUXURY_BALL', 'ITEM_PREMIER_BALL',
        }
        self.assertLessEqual(balls, set(entries))
        self.assertLessEqual({
            'ITEM_LAVA_COOKIE', 'ITEM_BLUE_FLUTE', 'ITEM_YELLOW_FLUTE',
            'ITEM_RED_FLUTE', 'ITEM_BLACK_FLUTE', 'ITEM_WHITE_FLUTE',
            'ITEM_BERRY_JUICE', 'ITEM_SACRED_ASH', 'ITEM_SHOAL_SALT',
            'ITEM_SHOAL_SHELL', 'ITEM_RED_SHARD', 'ITEM_BLUE_SHARD',
            'ITEM_YELLOW_SHARD', 'ITEM_GREEN_SHARD',
        }, set(entries))
        makefile = (demo.ROOT / 'Makefile').read_text()
        self.assertRegex(makefile, r'build/learner_demo/lesson\.s:.*language_learning/items\.json')
        self.assertRegex(makefile, r'build/learner_demo/lesson\.s:.*include/constants/items\.h')
        self.assertRegex(makefile, r'build/learner_demo/lesson\.s:.*src/party_menu\.c')
        constants = (demo.ROOT / 'include/constants/items.h').read_text()
        named_items = set(re.findall(r'^#define (ITEM_[A-Z0-9_]+) \d+$',
                                         constants, re.MULTILINE))
        named_items = {item for item in named_items
                       if item != 'ITEM_NONE' and not re.fullmatch(r'ITEM_[0-9A-F]{3}', item)}
        self.assertEqual(set(entries) | set(machines), named_items)
        item_ids = {item: int(number) for item, number in re.findall(
            r'^#define (ITEM_[A-Z0-9_]+) (\d+)$', constants, re.MULTILINE)}
        self.assertEqual(table_items, sorted(table_items, key=item_ids.get))
        self.assertIn('while (low < high)', code)
        key_section = constants.split('// Key Items', 1)[1].split('// TMs/HMs', 1)[0]
        key_items = set(re.findall(r'^#define (ITEM_[A-Z_0-9]+) \d+$',
                                   key_section, re.MULTILINE)) - {'ITEM_10B'}
        self.assertEqual(len(key_items), 29)
        self.assertLessEqual(key_items, set(entries))
        machine_constants = set(re.findall(r'^#define (ITEM_(?:TM|HM)\d{2}_[A-Z0-9_]+) \d+$',
                                               constants, re.MULTILINE))
        self.assertEqual(set(machines), machine_constants)
        held_section = constants.split('// hold items', 1)[1].split('// Key Items', 1)[0]
        held_items = set(re.findall(r'^#define (ITEM_(?!0)[A-Z0-9_]+) \d+$',
                                    held_section, re.MULTILINE))
        self.assertLessEqual(held_items, set(entries))
        berry_constants = set(re.findall(
            r'^#define (ITEM_[A-Z0-9_]+) \d+$',
            constants.split('#define ITEM_CHERI_BERRY', 1)[1].split('#define ITEM_0B0', 1)[0],
            re.MULTILINE))
        berry_constants.add('ITEM_CHERI_BERRY')
        self.assertEqual(len(berry_constants), 43)
        self.assertLessEqual(berry_constants, set(entries))
        for item, languages in {**entries, **machines}.items():
            self.assertRegex(constants, rf'(?m)^#define {item} \d+$')
            for tag, mapping, glyphs in [('ru', self.russian, self.glyphs), ('de', self.latin, {})]:
                self.assertEqual(len(demo.wrap(languages[tag]['name'], mapping, glyphs, 88)), 1)
                self.assertLessEqual(len(demo.wrap(languages[tag]['description'], mapping, glyphs, 104)), 2)

    def test_sprite_sheet_stream_and_loader_keep_native_size(self):
        for tag in ('ru', 'de'):
            raw = graphic_labels.tile_bytes(graphic_labels.render('dex_sprites', tag))
            stream = graphic_labels.literal_lz(raw)
            self.assertEqual(stream[0], 0x10)
            size = stream[1] | stream[2] << 8 | stream[3] << 16
            self.assertEqual(size, 0x1F00)
            decoded = []
            cursor = 4
            while len(decoded) < size:
                self.assertEqual(stream[cursor], 0)
                decoded.extend(stream[cursor + 1:cursor + 9])
                cursor += 9
            self.assertEqual(decoded, raw)
        storage = (demo.ROOT / 'src/pokemon_storage_system_2.c').read_text()
        self.assertIn('gLearnerStorageMiscTilesRu', storage)
        self.assertIn('gLearnerStorageMiscTilesDe', storage)
        party = (demo.ROOT / 'src/party_menu.c').read_text(encoding='utf-8')
        self.assertIn('gLearnerPartyMiscTilesRu', party)
        self.assertIn('gLearnerPartyMiscTilesDe', party)

    def test_bag_action_templates_keep_item_quantity_and_fit_pane(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        for key in ('gOtherText_OkayToThrowAwayPrompt', 'gOtherText_ThrewAwayItem', 'gOtherText_DepositedItems'):
            e = templates[key]
            self.assertEqual(e['max_width'], 104)
            for tag, mapping, glyphs, font in [('ru', self.russian, self.glyphs, 0), ('de', self.latin, {}, 3)]:
                data = bytes(field_templates.compile_text(e[tag], mapping, glyphs, font, e['widths'], e['max_width']))
                for token in (2, 3):
                    self.assertIn(bytes([0xFD, token, 0xFC, 6, font]), data)
                self.assertEqual(data.count(b'\xfe'), 1)
        code = (demo.ROOT / 'src/item_menu.c').read_text().split('static void sub_80A4A98(')[1].split('\n}\n')[0]
        self.assertIn('StringExpandPlaceholders(gStringVar4, translated)', code)
        self.assertIn('Menu_PrintTextPixelCoords(gStringVar4, 4, 104, 0)', code)

    def test_shared_display_hooks_and_new_game_only_tutorial(self):
        bag = (demo.ROOT / 'src/item_menu.c').read_text()
        self.assertIn('BagItemName(gCurrentBagPocketItemSlots[r4].itemId)', bag)
        self.assertIn('Learner_ItemText(itemId, TRUE)', bag)
        script = (demo.ROOT / 'src/scrcmd.c').read_text()
        self.assertIn('Learner_CopyItemName(itemId, sScriptStringVars[stringVarIndex])', script)
        dex = (demo.ROOT / 'src/pokedex.c').read_text()
        self.assertIn('DexLearnerText(sDexSearchColorOptions[var].title)', dex)
        settings = (demo.ROOT / 'language_learning/integration/lesson_script.inc').read_text()
        self.assertNotIn('multichoice 0, 0, MULTI_LEARNER_MODE', settings)
        self.assertIn('sLearnerMode == 1', (demo.ROOT / 'src/learner_intro.inc').read_text())

    def test_pc_startup_and_storage_primary_menu_use_selected_language(self):
        script_menu = (demo.ROOT / 'src/script_menu.c').read_text()
        self.assertIn('Learner_Translate(Text_WhichPCShouldBeAccessed)', script_menu)
        storage = (demo.ROOT / 'src/pokemon_storage_system.c').read_text()
        self.assertIn('translatedActions[i].text = StorageLearnerText(', storage)
        self.assertGreaterEqual(storage.count('StorageLearnerText(gUnknown_083B600C['), 6)
        self.assertIn('StorageLearnerText(gPCText_PartyFull2)', storage)
        self.assertIn('StorageLearnerText(gPCText_OnlyOne)', storage)

    def test_player_pc_item_storage_and_mailbox_menus_use_selected_language(self):
        player_pc = (demo.ROOT / 'src/player_pc.c').read_text()
        self.assertIn('translatedActions[i].text = PlayerPCLearnerText(sPlayerPCMenuActions[i].text)', player_pc)
        self.assertIn('translatedActions[i].text = PlayerPCLearnerText(gPCText_ItemPCOptionsText[i].text)', player_pc)
        self.assertIn('translatedActions[i].text = PlayerPCLearnerText(gMailboxMailOptions[i].text)', player_pc)
        self.assertIn('Menu_PrintText(PlayerPCLearnerText(gPCText_Mailbox)', player_pc)
        self.assertIn('Menu_PrintText(PlayerPCLearnerText(gPCText_ItemPCOptionsText[var].text)', player_pc)
        self.assertIn('Menu_PrintText(PlayerPCLearnerText(textPtr)', player_pc)

    def test_shop_and_decoration_action_menus_use_selected_language(self):
        shop = (demo.ROOT / 'src/shop.c').read_text()
        self.assertIn('translatedActions[i].text = ShopLearnerText(sBuySellQuitMenuActions[i].text)', shop)
        self.assertEqual(shop.count('Menu_PrintItemsReordered(1, 1,'), 4)
        decoration = (demo.ROOT / 'src/decoration.c').read_text()
        self.assertIn('translatedActions[i].text = DecorationLearnerText(gUnknown_083EC604[i].text)', decoration)
        self.assertIn('DecorationLearnerText(gUnknown_083EC624[gUnknown_020388D4])', decoration)

    def test_script_choice_windows_measure_translated_labels(self):
        script_menu = (demo.ROOT / 'src/script_menu.c').read_text()
        width_helper = script_menu.rsplit('static u16 GetStringWidthInTilesForScriptMenu', 1)[1].split('\n}', 1)[0]
        self.assertIn('str = Learner_Translate(str);', width_helper)

    def test_secret_base_and_link_trade_text_is_bilingual(self):
        entries = validate.load(demo.ROOT / 'language_learning/ui_sources.json')
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        required = {
            'SecretBaseText_DelRegist', 'TradeText_Cancel', 'TradeText_ChoosePoke',
            'TradeText_Summary1', 'TradeText_Trade1', 'TradeText_CancelTradePrompt',
            'TradeText_PressBToExit', 'TradeText_Summary2', 'TradeText_Trade2',
            'TradeText_LinkStandby', 'TradeText_TradeCancelled', 'TradeText_OnlyPoke',
            'TradeText_NonTradablePoke', 'TradeText_WaitingForFriend',
            'TradeText_WantToTrade', 'gTradeText_WillBeSent', 'gTradeText_ByeBye',
            'gTradeText_SentOverPoke', 'gTradeText_TakeGoodCare',
            'gTradeText_TradeOkayPrompt'
        }
        self.assertTrue(required.issubset(set(entries) | set(templates)))

    def test_pokeblock_case_labels_and_messages_are_bilingual(self):
        entries = validate.load(demo.ROOT / 'language_learning/ui_sources.json')
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        colors = {
            'Red', 'Blue', 'Pink', 'Green', 'Yellow', 'Purple', 'Indigo',
            'Brown', 'LiteBlue', 'Olive', 'Gray', 'Black', 'White', 'Gold'
        }
        for color in colors:
            self.assertIn(f'ContestStatsText_{color}PokeBlock', entries)
        for label in ('Spicy', 'Dry', 'Sweet', 'Bitter', 'Sour', 'Tasty', 'Feel', 'StowCase'):
            self.assertIn(f'gContestStatsText_{label}', entries)
        for message in ('ThrowAwayPrompt', 'WasThrownAway', 'NormallyAte',
                        'HappilyAte', 'DisdainfullyAte'):
            self.assertIn(f'gContestStatsText_{message}', templates)

    def test_contest_result_screens_use_selected_language(self):
        entries = validate.load(demo.ROOT / 'language_learning/ui_sources.json')
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        for label in ('AnnounceResults', 'PreliminaryResults', 'Round2Results'):
            self.assertIn(f'gContestText_{label}', entries)
        self.assertIn('gContestText_PokeWon', templates)
        self.assertIn('gContestText_ContestWinner', templates)
        source = (demo.ROOT / 'src/contest_link_util.c').read_text()
        self.assertGreaterEqual(source.count('ContestLearnerText(gContestText_'), 6)

    def test_contest_registration_and_ceremony_dialogue_is_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        required = {
            'FallarborTown_ContestLobby_Text_1A5DFC',
            'FallarborTown_ContestLobby_Text_1A5E46',
            'FallarborTown_ContestLobby_Text_EnterWhichPokemon1',
            'LilycoveCity_ContestLobby_Text_MonNotQualifiedForRank',
            'LilycoveCity_ContestLobby_Text_EggCannotTakePart',
            'LilycoveCity_ContestLobby_Text_ConfirmContestMon',
            'LinkContestRoom1_Text_1A68F0', 'LinkContestRoom1_Text_1A6976',
            'LinkContestRoom1_Text_1A6A04', 'LinkContestRoom1_Text_1A6A1F',
            'LinkContestRoom1_Text_1A6AE1', 'LinkContestRoom1_Text_1A6AF5',
            'LinkContestRoom1_Text_1A6C06', 'LinkContestRoom1_Text_1A6C21',
            'LinkContestRoom1_Text_1A6C9D', 'LinkContestRoom1_Text_1A6D16',
            'LinkContestRoom1_Text_1A6D3C', 'LinkContestRoom1_Text_1A6D6A',
            'LinkContestRoom1_Text_1A6D96', 'LinkContestRoom1_Text_1A6DAC',
            'LinkContestRoom1_Text_1A6DC5', 'LinkContestRoom1_Text_1A6DF1',
            'LinkContestRoom1_Text_1A6E1F'
        }
        self.assertTrue(required.issubset(templates))

    def test_contest_hall_and_berry_blender_dialogue_is_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        required = {
            'FallarborTown_ContestLobby_Text_1B6E63',
            'FallarborTown_ContestLobby_Text_1B6ED0',
            'FallarborTown_ContestLobby_Text_1B6F1F',
            'FallarborTown_ContestLobby_Text_1B6FF0',
            'FallarborTown_ContestLobby_Text_1B717C',
            'FallarborTown_ContestLobby_Text_1B71D2',
            'BerryBlender_Text_WhatKindOfPokeblockWillIGet',
            'FallarborTown_ContestLobby_Text_1B727C',
            'FallarborTown_ContestLobby_Text_1B7304',
            'FallarborTown_ContestLobby_Text_1B733B',
            'FallarborTown_ContestLobby_Text_1B7347',
            'FallarborTown_ContestLobby_Text_1B735A',
            'FallarborTown_ContestLobby_Text_UsedToHaveSketch',
            'FallarborTown_ContestLobby_Text_ICreateSketches',
            'FallarborTown_ContestHall_Text_DoAllRightInPreliminary',
            'FallarborTown_ContestHall_Text_MonAllTheseRibbons',
            'FallarborTown_ContestHall_Text_CantWinEverywhere',
            'FallarborTown_ContestHall_Text_SuperRankStage',
            'LilycoveCity_ContestLobby_Text_ProgressWillBeSaved',
            'LilycoveCity_ContestLobby_Text_TransmissionErrorTryAgain'
        }
        self.assertTrue(required.issubset(templates))

    def test_remaining_contest_guidance_and_registration_is_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        required = {
            'LilycoveCity_ContestLobby_Text_ExplainContests',
            'LilycoveCity_ContestLobby_Text_ExplainContestTypes',
            'LilycoveCity_ContestLobby_Text_ExplainContestRanks',
            'FallarborTown_ContestLobby_Text_1A6340',
            'LilycoveCity_ContestLobby_Text_RegistrationsFromFourNeedContestPass',
            'FallarborTown_ContestLobby_Text_1A64F4',
            'FallarborTown_ContestLobby_Text_1B704A',
            'FallarborTown_ContestLobby_Text_1B742F',
            'FallarborTown_ContestLobby_Text_1B7469',
            'ContestHall_Text_OnlyRegister4Players',
            'LilycoveCity_ContestLobby_Text_Explain4PlayerContest',
            'LilycoveCity_ContestLobby_Text_YourMonIsEntryNumX',
            'LilycoveCity_ContestLobby_Text_ReceivedARibbon',
            'LilycoveCity_ContestLobby_Text_PutTheRibbonOnMon'
        }
        self.assertTrue(required.issubset(templates))

    def test_lilycove_contest_painter_and_spectators_are_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        required = {
            'LilycoveCity_ContestLobby_Text_YourPokemonSpurredMeToPaint',
            'LilycoveCity_ContestLobby_Text_ShouldITakePaintingToMuseum',
            'LilycoveCity_ContestLobby_Text_IllTakePaintingToMuseum',
            'LilycoveCity_ContestLobby_Text_TakeMementoOfPainting',
            'LilycoveCity_ContestLobby_Text_TakeHomeButIdLikeToTakeToMuseum',
            'LilycoveCity_ContestLobby_Text_FineThatsTheWayItIs',
            'LilycoveCity_ContestLobby_Text_MasterRankHereICome',
            'LilycoveCity_ContestLobby_Text_WholeVarietyOfPokemonHere',
            'LilycoveCity_ContestLobby_Text_GetContestPassVerdanturf',
            'LilycoveCity_ContestLobby_Text_EyesOpenToMon',
            'LilycoveCity_ContestLobby_Text_ToughContestIsExtreme',
            'LilycoveCity_ContestLobby_Text_LavishedCareOnMon',
            'LilycoveCity_ContestLobby_Text_MadePokeblocksWithFamily'
        }
        self.assertTrue(required.issubset(templates))

    def test_lilycove_museum_first_floor_is_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        required = {
            'LilycoveCity_LilycoveMuseum_1F_Text_WelcomeToLilycoveMuseum',
            'LilycoveCity_LilycoveMuseum_1F_Text_ImCuratorHaveYouViewedOurPaintings',
            'LilycoveCity_LilycoveMuseum_1F_Text_NotDisturbYouTakeYourTime',
            'LilycoveCity_LilycoveMuseum_1F_Text_HaveYouAnInterestInPaintings',
            'LilycoveCity_LilycoveMuseum_1F_Text_HonoredYoudVisitInSpiteOfThat',
            'LilycoveCity_LilycoveMuseum_1F_Text_ExcellentCanYouComeWithMe',
            'LilycoveCity_LilycoveMuseum_1F_Text_VeryOldPainting',
            'LilycoveCity_LilycoveMuseum_1F_Text_OddLandscapeFantasticScenery',
            'LilycoveCity_LilycoveMuseum_1F_Text_PaintingOfBeautifulWoman',
            'LilycoveCity_LilycoveMuseum_1F_Text_PaintingOfLegendaryPokemon',
            'LilycoveCity_LilycoveMuseum_1F_Text_PaintingOfGrassPokemon',
            'LilycoveCity_LilycoveMuseum_1F_Text_PaintingOfBerries',
            'LilycoveCity_LilycoveMuseum_Text_BirdPokemonSculptureReplica',
            'LilycoveCity_LilycoveMuseum_1F_Text_BigPokeBallCarvedFromStone',
            'LilycoveCity_LilycoveMuseum_1F_Text_StoneTabletWithAncientText',
            'UnknownString_818788B',
            'LilycoveCity_LilycoveMuseum_1F_Text_MustntForgetLoveForFineArts',
            'LilycoveCity_LilycoveMuseum_1F_Text_ThisMuseumIsInspiration',
            'LilycoveCity_LilycoveMuseum_1F_Text_ThisLadyIsPretty',
            'LilycoveCity_LilycoveMuseum_1F_Text_ThisPokemonIsAdorable',
            'LilycoveCity_LilycoveMuseum_1F_Text_HeardMuseumGotNewPaintings',
            'LilycoveCity_LilycoveMuseum_1F_Text_CuratorHasBeenCheerful',
            'LilycoveCity_LilycoveMuseum_1F_Text_AimToSeeGreatPaintings',
            'LilycoveCity_LilycoveMuseum_1F_Text_MuseumTouristDestination'
        }
        self.assertTrue(required.issubset(templates))

    def test_lilycove_museum_second_floor_is_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        required = {
            'LilycoveCity_LilycoveMuseum_2F_Text_ThisIsExhibitHall',
            'LilycoveCity_LilycoveMuseum_2F_Text_ExplainExhibitHall',
            'LilycoveCity_LilycoveMuseum_2F_Text_PleaseObtainPaintingsForExhibit',
            'LilycoveCity_LilycoveMuseum_2F_Text_WishToFillExhibit',
            'LilycoveCity_LilycoveMuseum_2F_Text_ThanksAddedNewPainting',
            'LilycoveCity_LilycoveMuseum_2F_Text_ItsYouPlayer',
            'LilycoveCity_LilycoveMuseum_2F_Text_PaintingsAttractedMoreGuests',
            'LilycoveCity_LilycoveMuseum_2F_Text_TokenOfGratitude',
            'UnknownString_8188148',
            'LilycoveCity_LilycoveMuseum_2F_Text_KeepThisForYou',
            'LilycoveCity_LilycoveMuseum_2F_Text_HonorToHaveYouVisit',
            'LilycoveCity_LilycoveMuseum_2F_Text_ItsPinkPictureFrame',
            'LilycoveCity_LilycoveMuseum_2F_Text_ItsYellowPictureFrame',
            'LilycoveCity_LilycoveMuseum_2F_Text_ItsBluePictureFrame',
            'LilycoveCity_LilycoveMuseum_2F_Text_ItsRedPictureFrame',
            'LilycoveCity_LilycoveMuseum_2F_Text_ItsGreenPictureFrame',
            'LilycoveCity_LilycoveMuseum_2F_Text_ItsPaintingOfPokemon',
            'LilycoveCity_LilycoveMuseum_2F_Text_NewPaintingsSurprisedMe',
            'LilycoveCity_LilycoveMuseum_2F_Text_NewPaintingsRatherAmusing',
            'LilycoveCity_LilycoveMuseum_2F_Text_ThesePaintingsOfYourPokemon'
        }
        self.assertTrue(required.issubset(templates))

    def test_lilycove_department_store_floors_are_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        required = {
            'LilycoveCity_DepartmentStore_1F_Text_WelcomeToDeptStore',
            'LilycoveCity_DepartmentStore_1F_Text_IBuyAllSortsOfThings',
            'LilycoveCity_DepartmentStore_1F_Text_MomBuyingMeFurniture',
            'LilycoveCity_DepartmentStore_1F_Text_BuyingSomethingForAzumarill',
            'LilycoveCity_DepartmentStore_1F_Text_Azumarill',
            'LilycoveCity_DepartmentStore_1F_Text_FloorNamesSign',
            'LilycoveCity_DepartmentStore_2F_Text_LearnToUseItemsProperly',
            'LilycoveCity_DepartmentStore_2F_Text_GoodGiftForHusband',
            'LilycoveCity_DepartmentStore_2F_Text_StockUpOnItems',
            'LilycoveCity_DepartmentStore_2F_Text_UnusedFloorInfo',
            'LilycoveCity_DepartmentStore_3F_Text_ItemsBestForTougheningPokemon',
            'LilycoveCity_DepartmentStore_3F_Text_WantMoreEndurance',
            'LilycoveCity_DepartmentStore_3F_Text_GaveCarbosToSpeedUpMon',
            'LilycoveCity_DepartmentStore_3F_Text_UnusedFloorInfo',
            'LilycoveCity_DepartmentStore_4F_Text_AttackOrDefenseTM',
            'LilycoveCity_DepartmentStore_4F_Text_FiftyDifferentTMs',
            'LilycoveCity_DepartmentStore_4F_Text_PokemonOnlyHaveFourMoves',
            'LilycoveCity_DepartmentStore_4F_Text_UnusedFloorInfo',
            'LilycoveCity_DepartmentStore_5F_Text_PlaceFullOfCuteDolls',
            'LilycoveCity_DepartmentStore_5F_Text_GettingDollInsteadOfPokemon',
            'LilycoveCity_DepartmentStore_5F_Text_SellManyCuteMatsHere',
            'LilycoveCity_DepartmentStore_5F_Text_UnusedFloorInfo',
            'LilycoveCity_DepartmentStoreRooftop_Text_SetDatesForClearOutSales',
            'LilycoveCity_DepartmentStoreRooftop_Text_BeenWaitingForClearOutSale',
            'LilycoveCity_DepartmentStoreRooftop_Text_BoneDryThirsty',
            'LilycoveCity_DepartmentStoreRooftop_Text_WhichDrinkWouldYouLike',
            'LilycoveCity_DepartmentStoreRooftop_Text_CanOfDrinkDroppedDown',
            'LilycoveCity_DepartmentStoreRooftop_Text_ExtraCanOfDrinkDroppedDown',
            'LilycoveCity_DepartmentStoreRooftop_Text_NotEnoughMoney',
            'LilycoveCity_DepartmentStoreRooftop_Text_DecidedAgainstBuyingDrink'
        }
        self.assertTrue(required.issubset(templates))

    def test_lilycove_department_store_lottery_is_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        required = {
            'LilycoveCity_DepartmentStore_1F_Text_LotteryCornerDrawTicket',
            'LilycoveCity_DepartmentStore_1F_Text_ComeBackTomorrow',
            'LilycoveCity_DepartmentStore_1F_Text_PleaseVisitAgain',
            'UnknownString_81C4C9F',
            'LilycoveCity_DepartmentStore_1F_Text_PleasePickTicket',
            'LilycoveCity_DepartmentStore_1F_Text_TicketNumberIsXPleaseWait',
            'LilycoveCity_DepartmentStore_1F_Text_TicketMatchesPartyMon',
            'LilycoveCity_DepartmentStore_1F_Text_TicketMatchesPCMon',
            'LilycoveCity_DepartmentStore_1F_Text_NoNumbersMatched',
            'LilycoveCity_DepartmentStore_1F_Text_TwoDigitsMatched',
            'LilycoveCity_DepartmentStore_1F_Text_ThreeDigitsMatched',
            'LilycoveCity_DepartmentStore_1F_Text_FourDigitsMatched',
            'LilycoveCity_DepartmentStore_1F_Text_AllFiveDigitsMatched',
            'LilycoveCity_DepartmentStore_1F_Text_NoRoomForThis',
            'LilycoveCity_DepartmentStore_1F_Text_PrizeWeveBeenHolding',
            'LilycoveCity_DepartmentStore_1F_Text_PleaseVisitAgain2'
        }
        self.assertTrue(required.issubset(templates))

    def test_lilycove_rival_and_outdoor_npcs_are_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        required = {
            'LilycoveCity_Text_MayShoppingLetsBattle',
            'LilycoveCity_Text_MayNotRaisingPokemon',
            'LilycoveCity_Text_MayBattleMe',
            'LilycoveCity_Text_MayWontBeBeaten',
            'LilycoveCity_Text_MayDefeat',
            'LilycoveCity_Text_MayGoingBackToLittleroot',
            'LilycoveCity_Text_MayYouGoingToCollectBadges',
            'LilycoveCity_Text_MayYouGoingToPokemonLeague',
            'LilycoveCity_Text_MayYouGoingToBattleTower',
            'LilycoveCity_Text_BrendanShoppingLetsBattle',
            'LilycoveCity_Text_BrendanNoConfidence',
            'LilycoveCity_Text_BrendanBattleMe',
            'LilycoveCity_Text_BrendanWontBeBeaten',
            'LilycoveCity_Text_BrendanDefeat',
            'LilycoveCity_Text_BrendanGoingBackToLittleroot',
            'LilycoveCity_Text_BrendanYouGoingToCollectBadges',
            'LilycoveCity_Text_BrendanYouGoingToPokemonLeague',
            'LilycoveCity_Text_BrendanYouGoingToBattleTower',
            'LilycoveCity_Text_MovedLootIntoHideoutToday',
            'LilycoveCity_Text_ChanceToDoBigThings',
            'LilycoveCity_Text_DontGoNearCaveInCove',
            'LilycoveCity_Text_IfWorldBecomesOurs',
            'LilycoveCity_Text_WailmerLeapOutOfWater',
            'LilycoveCity_Text_GetLostMessingUpTraining',
            'LilycoveCity_Text_ContestHallInTown',
            'LilycoveCity_Text_StrangeCaveInCove',
            'LilycoveCity_Text_GoingToMoveDeleterForHMs',
            'LilycoveCity_Text_ImFromKanto',
            'LilycoveCity_Text_EvilTeamBeenTrainingWailmer',
            'LilycoveCity_Text_SomeonePuntedEvilTeamOut',
            'LilycoveCity_Text_SomeoneStoleMyPokemon'
        }
        self.assertTrue(required.issubset(templates))

    def test_lilycove_remaining_outdoor_dialogue_and_signs_are_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        required = {
            'LilycoveCity_Text_MissingPokemonCameBack',
            'LilycoveCity_Text_ImArtDealer',
            'LilycoveCity_Text_SeaRemainsForeverYoung',
            'LilycoveCity_Text_SixtyYearsAgoHusbandProposed',
            'LilycoveCity_Text_EvilTeamRenovatedCavern',
            'LilycoveCity_Text_EvilTeamLotGoneForGood',
            'LilycoveCity_Text_CitySign',
            'LilycoveCity_Text_ContestHallSign',
            'LilycoveCity_Text_MotelSign',
            'LilycoveCity_Text_MuseumSign',
            'LilycoveCity_Text_MuseumSignPlayersExhibit',
            'LilycoveCity_Text_HarborSignUnderConstruction',
            'LilycoveCity_Text_HarborSign',
            'LilycoveCity_Text_TrainerFanClubSign',
            'LilycoveCity_Text_DepartmentStoreSign',
            'LilycoveCity_Text_MoveDeletersHouseSign'
        }
        self.assertTrue(required.issubset(templates))

    def test_lilycove_center_harbor_and_motel_are_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        required = {
            'LilycoveCity_PokemonCenter_1F_Text_HowManyKindsOfPokemon',
            'LilycoveCity_PokemonCenter_1F_Text_HeardAboutRottenScoundrels',
            'LilycoveCity_PokemonCenter_1F_Text_HaventSeenRottenScoundrels',
            'UnknownString_818A10A',
            'UnknownString_818A168',
            'LilycoveCity_Harbor_Text_FerryUnavailable',
            'LilycoveCity_Harbor_Text_MayISeeYourTicket',
            'LilycoveCity_Harbor_Text_NoTicket',
            'LilycoveCity_Harbor_Text_FlashTicketWhereTo',
            'LilycoveCity_Harbor_Text_SailAnotherTime',
            'LilycoveCity_Harbor_Text_SlateportItIs',
            'LilycoveCity_Harbor_Text_BattleTowerItIs',
            'LilycoveCity_Harbor_Text_PleaseBoard',
            'LilycoveCity_Harbor_Text_WhereWouldYouLikeToGo',
            'LilycoveCity_Harbor_Text_SailorFerryUnavailable',
            'LilycoveCity_Harbor_Text_SailorFerryAvailable',
            'LilycoveCity_CoveLilyMotel_1F_Text_GuestsDoubledByMascot',
            'LilycoveCity_CoveLilyMotel_1F_Text_NoGuestsWithEvilTeam',
            'LilycoveCity_CoveLilyMotel_1F_Text_CantSeeTheTV',
            'LilycoveCity_CoveLilyMotel_1F_Text_MonFoundLostItem',
            'LilycoveCity_CoveLilyMotel_1F_Text_HeardEvilTeamHideoutBusted',
            'LilycoveCity_CoveLilyMotel_1F_Text_HouseSittingMonCaughtBurglar',
            'LilycoveCity_CoveLilyMotel_1F_Text_BetterGetWorkingOnGuestsDinner',
            'LilycoveCity_CoveLilyMotel_2F_Text_ShowMeCompletedDex',
            'LilycoveCity_CoveLilyMotel_2F_Text_FilledPokedexGiveYouThis',
            'LilycoveCity_CoveLilyMotel_2F_Text_ImTheProgrammer',
            'LilycoveCity_CoveLilyMotel_2F_Text_ImTheGraphicArtist',
            'LilycoveCity_CoveLilyMotel_2F_Text_GirlsAreCute',
            'LilycoveCity_CoveLilyMotel_2F_Text_SeaBreezeTicklesHeart',
            'LilycoveCity_CoveLilyMotel_2F_Text_NeverLeaveWithoutGameBoy'
        }
        self.assertTrue(required.issubset(templates))

    def test_lilycove_houses_and_move_deleter_are_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        required = {
            'LilycoveCity_House1_Text_PokemonPartnersNotTools',
            'LilycoveCity_House1_Text_Kecleon',
            'LilycoveCity_House2_Text_NotAwakeYetHaveThis',
            'LilycoveCity_House2_Text_SleepIsEssential',
            'LilycoveCity_House3_Text_LearnFromMasterOfPokeblocks',
            'LilycoveCity_House3_Text_OhAreYouSure',
            'LilycoveCity_House3_Text_ExplainPokeblocks',
            'LilycoveCity_House3_Text_HappyToHaveQuadruplets',
            'LilycoveCity_House3_Text_GoingToWinMultiBattles',
            'LilycoveCity_House3_Text_LikeMixingAtRecordCorner',
            'LilycoveCity_House3_Text_MakePokeblocksWithBerryBlender',
            'LilycoveCity_House3_Text_GoingToEnterContest',
            'LilycoveCity_House4_Text_MysteriesAtBottomOfSea',
            'LilycoveCity_House4_Text_UnderwaterTrenchMossdeepSootopolis',
            'LilycoveCity_MoveDeletersHouse_Text_ICanMakeMonForgetMove',
            'LilycoveCity_MoveDeletersHouse_Text_WhichMonShouldForget',
            'LilycoveCity_MoveDeletersHouse_Text_WhichMoveShouldBeForgotten',
            'LilycoveCity_MoveDeletersHouse_Text_MonOnlyKnowsOneMove',
            'LilycoveCity_MoveDeletersHouse_Text_MonsMoveShouldBeForgotten',
            'LilycoveCity_MoveDeletersHouse_Text_MonHasForgottenMove',
            'LilycoveCity_MoveDeletersHouse_Text_ComeAgain',
            'LilycoveCity_MoveDeletersHouse_Text_EggCantForgetMoves'
        }
        self.assertTrue(required.issubset(templates))

    def test_lilycove_trainer_fan_club_is_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        required = {
            'LilycoveCity_PokemonTrainerFanClub_Text_OhWowItsPlayer',
            'LilycoveCity_PokemonTrainerFanClub_Text_HeardAboutYouImYourFan',
            'LilycoveCity_PokemonTrainerFanClub_Text_YoureOneWeWantToWin',
            'LilycoveCity_PokemonTrainerFanClub_Text_OthersDontKnowYoureTheBest',
            'LilycoveCity_PokemonTrainerFanClub_Text_TrainersPowerIsOutOfTheOrdinary',
            'LilycoveCity_PokemonTrainerFanClub_Text_TrainerIsBestNoOneWantsToListen',
            'LilycoveCity_PokemonTrainerFanClub_Text_HearingAboutToughNewTrainer',
            'LilycoveCity_PokemonTrainerFanClub_Text_ImPullingForYou',
            'LilycoveCity_PokemonTrainerFanClub_Text_BrawlyNoImYourFan',
            'LilycoveCity_PokemonTrainerFanClub_Text_ICantHelpLikingBrawly',
            'LilycoveCity_PokemonTrainerFanClub_Text_NobodyUnderstandsBrawly',
            'LilycoveCity_PokemonTrainerFanClub_Text_MyFavoriteTrainerIsBrawly',
            'LilycoveCity_PokemonTrainerFanClub_Text_YouveSurpassedYourFather',
            'LilycoveCity_PokemonTrainerFanClub_Text_YourFatherNeverGaveUpSoKeepOnBattling',
            'LilycoveCity_PokemonTrainerFanClub_Text_LongWayToGoComparedToNorman',
            'LilycoveCity_PokemonTrainerFanClub_Text_YouAndNormanAreDifferent',
            'LilycoveCity_PokemonTrainerFanClub_Text_WeDiscussStrongestTrainers',
            'LilycoveCity_PokemonTrainerFanClub_Text_OhWoweeItsPlayer',
            'LilycoveCity_PokemonTrainerFanClub_Text_AlwaysCheerForYou',
            'LilycoveCity_PokemonTrainerFanClub_Text_EveryoneThinksTrainerIsCool',
            'LilycoveCity_PokemonTrainerFanClub_Text_TrainerIsReallyCoolItsJustMe',
            'LilycoveCity_PokemonTrainerFanClub_Text_WishThereWasTrainerLikeThat',
            'LilycoveCity_PokemonTrainerFanClub_Text_WantToBeStrongLikeYou',
            'LilycoveCity_PokemonTrainerFanClub_Text_OnlyOneWhoCheersForYou',
            'LilycoveCity_PokemonTrainerFanClub_Text_TrainerIsWickedlyCool',
            'LilycoveCity_PokemonTrainerFanClub_Text_NeverGoingToStopBeingTrainersFan',
            'LilycoveCity_PokemonTrainerFanClub_Text_YoureAmazingAfterAll',
            'LilycoveCity_PokemonTrainerFanClub_Text_ImInYourCorner',
            'LilycoveCity_PokemonTrainerFanClub_Text_ThinkTrainerIsNumberOne',
            'LilycoveCity_PokemonTrainerFanClub_Text_YoureMaybeStrongerThanTrainer',
            'LilycoveCity_PokemonTrainerFanClub_Text_YouChangedMyMind',
            'LilycoveCity_PokemonTrainerFanClub_Text_YouBattleAttractivelyInToughSituation',
            'LilycoveCity_PokemonTrainerFanClub_Text_TrainerIsStandout',
            'LilycoveCity_PokemonTrainerFanClub_Text_NoOneCanKnockYouButTrainerStronger',
            'LilycoveCity_PokemonTrainerFanClub_Text_YouImpressive',
            'LilycoveCity_PokemonTrainerFanClub_Text_OnlyIRecognizeYourTrueWorth',
            'LilycoveCity_PokemonTrainerFanClub_Text_HaventRealizedPotential',
            'LilycoveCity_PokemonTrainerFanClub_Text_YourePowerfulButNotTrueStrength'
        }
        self.assertTrue(required.issubset(templates))

    def test_lilycove_contest_hall_is_fully_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        source = (demo.ROOT / 'data/maps/LilycoveCity_ContestHall/text.inc').read_text()
        symbols = set(re.findall(r'^([A-Za-z_]\w*)::', source, re.MULTILINE))
        self.assertEqual(37, len(symbols))
        self.assertTrue(symbols.issubset(templates))

    def test_route_121_is_fully_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        source = (demo.ROOT / 'data/maps/Route121/text.inc').read_text(errors='replace')
        symbols = set(re.findall(r'^([A-Za-z_]\w*)::', source, re.MULTILINE))
        self.assertEqual(4, len(symbols))
        self.assertTrue(symbols.issubset(templates))

    def test_mt_pyre_first_two_floors_are_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        symbols = set()
        for floor in ('MtPyre_1F', 'MtPyre_2F'):
            source = (demo.ROOT / f'data/maps/{floor}/text.inc').read_text(errors='replace')
            symbols.update(re.findall(r'^([A-Za-z_]\w*)::', source, re.MULTILINE))
        self.assertEqual(17, len(symbols))
        self.assertTrue(symbols.issubset(templates))

    def test_mt_pyre_upper_floors_are_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        symbols = set()
        for floor in ('MtPyre_3F', 'MtPyre_4F', 'MtPyre_5F', 'MtPyre_6F'):
            source = (demo.ROOT / f'data/maps/{floor}/text.inc').read_text(errors='replace')
            symbols.update(re.findall(r'^([A-Za-z_]\w*)::', source, re.MULTILINE))
        self.assertEqual(18, len(symbols))
        self.assertTrue(symbols.issubset(templates))

    def test_aqua_hideout_is_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        symbols = set()
        for floor in ('AquaHideout_1F', 'AquaHideout_B1F', 'AquaHideout_B2F'):
            source = (demo.ROOT / f'data/maps/{floor}/text.inc').read_text(errors='replace')
            symbols.update(re.findall(r'^([A-Za-z_]\w*)::', source, re.MULTILINE))
        self.assertEqual(26, len(symbols))
        self.assertTrue(symbols.issubset(templates))

    def test_route_124_is_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        symbols = set()
        for area in ('Route124', 'Route124_DivingTreasureHuntersHouse'):
            source = (demo.ROOT / f'data/maps/{area}/text.inc').read_text(errors='replace')
            symbols.update(re.findall(r'^([A-Za-z_]\w*)::', source, re.MULTILINE))
        self.assertEqual(12, len(symbols))
        self.assertTrue(symbols.issubset(templates))

    def test_mossdeep_city_exterior_is_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        source = (demo.ROOT / 'data/maps/MossdeepCity/text.inc').read_text(errors='replace')
        symbols = set(re.findall(r'^([A-Za-z_]\w*)::', source, re.MULTILINE))
        self.assertEqual(15, len(symbols))
        self.assertTrue(symbols.issubset(templates))

    def test_mossdeep_city_houses_are_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        symbols = set()
        for house in ('House1', 'House2', 'House3', 'House4'):
            source = (demo.ROOT / f'data/maps/MossdeepCity_{house}/text.inc').read_text(errors='replace')
            symbols.update(re.findall(r'^([A-Za-z_]\w*)::', source, re.MULTILINE))
        self.assertEqual(17, len(symbols))
        self.assertTrue(symbols.issubset(templates))

    def test_mossdeep_city_services_are_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        symbols = set()
        areas = ('MossdeepCity_Mart', 'MossdeepCity_PokemonCenter_1F',
                 'MossdeepCity_PokemonCenter_2F', 'MossdeepCity_SpaceCenter_1F',
                 'MossdeepCity_SpaceCenter_2F')
        for area in areas:
            source = (demo.ROOT / f'data/maps/{area}/text.inc').read_text(errors='replace')
            symbols.update(re.findall(r'^([A-Za-z_]\w*)::', source, re.MULTILINE))
        self.assertEqual(16, len(symbols))
        self.assertTrue(symbols.issubset(templates))

    def test_stevens_house_is_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        source = (demo.ROOT / 'data/maps/MossdeepCity_StevensHouse/text.inc').read_text(errors='replace')
        symbols = set(re.findall(r'^([A-Za-z_]\w*)::', source, re.MULTILINE))
        self.assertEqual(10, len(symbols))
        self.assertTrue(symbols.issubset(templates))

    def test_mossdeep_game_corner_is_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        source = (demo.ROOT / 'data/maps/MossdeepCity_GameCorner_1F/text.inc').read_text(errors='replace')
        symbols = set(re.findall(r'^([A-Za-z_]\w*)::', source, re.MULTILINE))
        self.assertEqual(11, len(symbols))
        self.assertTrue(symbols.issubset(templates))

    def test_mossdeep_gym_is_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        source = (demo.ROOT / 'data/maps/MossdeepCity_Gym/text.inc').read_text(errors='replace')
        symbols = set(re.findall(r'^([A-Za-z_]\w*)::', source, re.MULTILINE))
        self.assertEqual(29, len(symbols))
        self.assertTrue(symbols.issubset(templates))

    def test_eastern_sea_story_is_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        symbols = set()
        areas = ('ShoalCave_LowTideLowerRoom', 'Route128', 'SeafloorCavern_Room1',
                 'SeafloorCavern_Room3', 'SeafloorCavern_Room4')
        for area in areas:
            source = (demo.ROOT / f'data/maps/{area}/text.inc').read_text(errors='replace')
            symbols.update(re.findall(r'^([A-Za-z_]\w*)::', source, re.MULTILINE))
        self.assertEqual(23, len(symbols))
        self.assertTrue(symbols.issubset(templates))

    def test_story_team_tokens_compile(self):
        text = '{GOOD_LEADER} {EVIL_LEADER} {GOOD_TEAM} {EVIL_TEAM}'
        widths = {'GOOD_LEADER': 32, 'EVIL_LEADER': 32, 'GOOD_TEAM': 24, 'EVIL_TEAM': 24}
        data = field_templates.compile_text(text, self.latin, {}, 3, widths)
        self.assertIn(11, data)
        self.assertIn(10, data)
        self.assertIn(9, data)
        self.assertIn(8, data)

    def test_sootopolis_houses_one_through_seven_are_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        symbols = set()
        for house in range(1, 8):
            source = (demo.ROOT / f'data/maps/SootopolisCity_House{house}/text.inc').read_text(errors='replace')
            symbols.update(re.findall(r'^([A-Za-z_]\w*)::', source, re.MULTILINE))
        self.assertEqual(22, len(symbols))
        self.assertTrue(symbols.issubset(templates))

    def test_sootopolis_size_house_and_services_are_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        symbols = set()
        for area in ('SootopolisCity_House8', 'SootopolisCity_Mart',
                     'SootopolisCity_PokemonCenter_1F'):
            source = (demo.ROOT / f'data/maps/{area}/text.inc').read_text(errors='replace')
            symbols.update(re.findall(r'^([A-Za-z_]\w*)::', source, re.MULTILINE))
        self.assertEqual(22, len(symbols))
        self.assertTrue(symbols.issubset(templates))

    def test_sootopolis_exterior_is_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        source = (demo.ROOT / 'data/maps/SootopolisCity/text.inc').read_text(errors='replace')
        symbols = set(re.findall(r'^([A-Za-z_]\w*)::', source, re.MULTILINE))
        self.assertEqual(32, len(symbols))
        self.assertTrue(symbols.issubset(templates))

    def test_sootopolis_gym_is_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        source = (demo.ROOT / 'data/maps/SootopolisCity_Gym_1F/text.inc').read_text(errors='replace')
        symbols = set(re.findall(r'^([A-Za-z_]\w*)::', source, re.MULTILINE))
        self.assertEqual(35, len(symbols))
        self.assertTrue(symbols.issubset(templates))

    def test_ever_grande_approach_and_victory_road_first_floor_are_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        symbols = set()
        areas = ('EverGrandeCity', 'EverGrandeCity_PokemonCenter_1F',
                 'EverGrandeCity_PokemonLeague', 'VictoryRoad_1F')
        for area in areas:
            source = (demo.ROOT / f'data/maps/{area}/text.inc').read_text(errors='replace')
            symbols.update(re.findall(r'^([A-Za-z_]\w*)::', source, re.MULTILINE))
        self.assertEqual(23, len(symbols))
        self.assertTrue(symbols.issubset(templates))

    def test_victory_road_lower_floors_are_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        symbols = set()
        for floor in ('VictoryRoad_B1F', 'VictoryRoad_B2F'):
            source = (demo.ROOT / f'data/maps/{floor}/text.inc').read_text(errors='replace')
            symbols.update(re.findall(r'^([A-Za-z_]\w*)::', source, re.MULTILINE))
        self.assertEqual(21, len(symbols))
        self.assertTrue(symbols.issubset(templates))

    def test_elite_four_champion_and_hall_of_fame_are_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        symbols = set()
        areas = ('EverGrandeCity_SidneysRoom', 'EverGrandeCity_PhoebesRoom',
                 'EverGrandeCity_GlaciasRoom', 'EverGrandeCity_DrakesRoom',
                 'EverGrandeCity_ChampionsRoom', 'EverGrandeCity_HallOfFame')
        for area in areas:
            source = (demo.ROOT / f'data/maps/{area}/text.inc').read_text(errors='replace')
            symbols.update(re.findall(r'^([A-Za-z_]\w*)::', source, re.MULTILINE))
        self.assertEqual(27, len(symbols))
        self.assertTrue(symbols.issubset(templates))

    def test_battle_tower_is_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        symbols = set()
        for area in ('BattleTower_Outside', 'BattleTower_Lobby',
                     'BattleTower_BattleRoom'):
            source = (demo.ROOT / f'data/maps/{area}/text.inc').read_text(errors='replace')
            symbols.update(re.findall(r'^([A-Za-z_]\w*)::', source, re.MULTILINE))
        self.assertEqual(50, len(symbols))
        self.assertTrue(symbols.issubset(templates))

    def test_ss_tidal_is_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        symbols = set()
        for area in ('SSTidalRooms', 'SSTidalCorridor', 'SSTidalLowerDeck'):
            source = (demo.ROOT / f'data/maps/{area}/text.inc').read_text(errors='replace')
            symbols.update(re.findall(r'^([A-Za-z_]\w*)::', source, re.MULTILINE))
        self.assertEqual(49, len(symbols))
        self.assertTrue(symbols.issubset(templates))

    def test_pacifidlog_town_is_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        symbols = set()
        areas = ('PacifidlogTown', 'PacifidlogTown_House1', 'PacifidlogTown_House2',
                 'PacifidlogTown_House3', 'PacifidlogTown_House4',
                 'PacifidlogTown_House5', 'PacifidlogTown_PokemonCenter_1F')
        for area in areas:
            source = (demo.ROOT / f'data/maps/{area}/text.inc').read_text(errors='replace')
            symbols.update(re.findall(r'^([A-Za-z_]\w*)::', source, re.MULTILINE))
        self.assertEqual(34, len(symbols))
        self.assertTrue(symbols.issubset(templates))

    def test_rustboro_city_exterior_is_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        source = (demo.ROOT / 'data/maps/RustboroCity/text.inc').read_text(errors='replace')
        symbols = set(re.findall(r'^([A-Za-z_]\w*)::?', source, re.MULTILINE))
        self.assertEqual(31, len(symbols))
        self.assertTrue(symbols.issubset(templates))

    def test_rustboro_gym_and_school_are_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        symbols = set()
        for area in ('RustboroCity_Gym', 'RustboroCity_PokemonSchool'):
            source = (demo.ROOT / f'data/maps/{area}/text.inc').read_text(errors='replace')
            symbols.update(re.findall(r'^([A-Za-z_]\w*)::', source, re.MULTILINE))
        self.assertEqual(31, len(symbols))
        self.assertTrue(symbols.issubset(templates))

    def test_rustboro_devon_corporation_is_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        symbols = set()
        for floor in ('RustboroCity_DevonCorp_1F', 'RustboroCity_DevonCorp_2F',
                      'RustboroCity_DevonCorp_3F'):
            source = (demo.ROOT / f'data/maps/{floor}/text.inc').read_text(errors='replace')
            symbols.update(re.findall(r'^([A-Za-z_]\w*)::', source, re.MULTILINE))
        self.assertEqual(36, len(symbols))
        self.assertTrue(symbols.issubset(templates))

    def test_rustboro_houses_and_services_are_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        symbols = set()
        areas = ('RustboroCity_House1', 'RustboroCity_House2', 'RustboroCity_House3',
                 'RustboroCity_Flat1_1F', 'RustboroCity_Flat1_2F',
                 'RustboroCity_Flat2_1F', 'RustboroCity_Flat2_2F',
                 'RustboroCity_Flat2_3F', 'RustboroCity_CuttersHouse',
                 'RustboroCity_Mart', 'RustboroCity_PokemonCenter_1F')
        for area in areas:
            source = (demo.ROOT / f'data/maps/{area}/text.inc').read_text(errors='replace')
            symbols.update(re.findall(r'^([A-Za-z_]\w*)::', source, re.MULTILINE))
        self.assertEqual(30, len(symbols))
        self.assertTrue(symbols.issubset(templates))

    def test_slateport_harbor_and_shipyard_are_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        symbols = set()
        for area in ('SlateportCity_Harbor', 'SlateportCity_SternsShipyard_1F',
                     'SlateportCity_SternsShipyard_2F'):
            source = (demo.ROOT / f'data/maps/{area}/text.inc').read_text(errors='replace')
            symbols.update(re.findall(r'^([A-Za-z_]\w*)::', source, re.MULTILINE))
        self.assertEqual(38, len(symbols))
        self.assertTrue(symbols.issubset(templates))

    def test_slateport_oceanic_museum_is_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        symbols = set()
        for floor in ('SlateportCity_OceanicMuseum_1F',
                      'SlateportCity_OceanicMuseum_2F'):
            source = (demo.ROOT / f'data/maps/{floor}/text.inc').read_text(errors='replace')
            symbols.update(re.findall(r'^([A-Za-z_]\w*)::', source, re.MULTILINE))
        self.assertEqual(55, len(symbols))
        self.assertTrue(symbols.issubset(templates))

    def test_slateport_city_exterior_is_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        source = (demo.ROOT / 'data/maps/SlateportCity/text.inc').read_text(errors='replace')
        symbols = set(re.findall(r'^([A-Za-z_]\w*)::', source, re.MULTILINE))
        self.assertEqual(61, len(symbols))
        self.assertTrue(symbols.issubset(templates))

    def test_slateport_houses_fan_club_and_services_are_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        symbols = set()
        areas = ('SlateportCity_PokemonFanClub', 'SlateportCity_House1',
                 'SlateportCity_House2', 'SlateportCity_Mart',
                 'SlateportCity_PokemonCenter_1F')
        for area in areas:
            source = (demo.ROOT / f'data/maps/{area}/text.inc').read_text(errors='replace')
            symbols.update(re.findall(r'^([A-Za-z_]\w*)::', source, re.MULTILINE))
        self.assertEqual(36, len(symbols))
        self.assertTrue(symbols.issubset(templates))

    def test_slateport_contest_hall_is_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        symbols = set()
        for area in ('SlateportCity_ContestLobby', 'SlateportCity_ContestHall'):
            source = (demo.ROOT / f'data/maps/{area}/text.inc').read_text(errors='replace')
            symbols.update(re.findall(r'^([A-Za-z_]\w*)::', source, re.MULTILINE))
        self.assertEqual(20, len(symbols))
        self.assertTrue(symbols.issubset(templates))

    def test_route_109_and_seashore_house_are_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        symbols = set()
        for area in ('Route109', 'Route109_SeashoreHouse'):
            source = (demo.ROOT / f'data/maps/{area}/text.inc').read_text(errors='replace')
            symbols.update(re.findall(r'^([A-Za-z_]\w*)::', source, re.MULTILINE))
        self.assertEqual(33, len(symbols))
        self.assertTrue(symbols.issubset(templates))

    def test_route_110_is_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        source = (demo.ROOT / 'data/maps/Route110/text.inc').read_text(errors='replace')
        symbols = set(re.findall(r'^([A-Za-z_]\w*)::', source, re.MULTILINE))
        self.assertEqual(39, len(symbols))
        self.assertTrue(symbols.issubset(templates))

    def test_trick_house_shared_rooms_are_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        symbols = set()
        for area in ('Route110_TrickHouseEntrance', 'Route110_TrickHouseEnd'):
            source = (demo.ROOT / f'data/maps/{area}/text.inc').read_text(errors='replace')
            symbols.update(re.findall(r'^([A-Za-z_]\w*)::', source, re.MULTILINE))
        self.assertEqual(39, len(symbols))
        self.assertTrue(symbols.issubset(templates))

    def test_trick_house_puzzles_one_through_four_are_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        symbols = set()
        for number in range(1, 5):
            source = (demo.ROOT / f'data/maps/Route110_TrickHousePuzzle{number}/text.inc').read_text(errors='replace')
            symbols.update(re.findall(r'^([A-Za-z_]\w*)::', source, re.MULTILINE))
        self.assertEqual(40, len(symbols))
        self.assertTrue(symbols.issubset(templates))

    def test_trick_house_puzzles_five_through_eight_are_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        symbols = set()
        for number in range(5, 9):
            source = (demo.ROOT / f'data/maps/Route110_TrickHousePuzzle{number}/text.inc').read_text(errors='replace')
            symbols.update(re.findall(r'^([A-Za-z_]\w*)::', source, re.MULTILINE))
        self.assertEqual(58, len(symbols))
        self.assertTrue(symbols.issubset(templates))

    def test_mauville_city_exterior_is_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        source = (demo.ROOT / 'data/maps/MauvilleCity/text.inc').read_text(errors='replace')
        symbols = set(re.findall(r'^([A-Za-z_]\w*)::', source, re.MULTILINE))
        self.assertEqual(28, len(symbols))
        self.assertTrue(symbols.issubset(templates))

    def test_mauville_gym_is_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        source = (demo.ROOT / 'data/maps/MauvilleCity_Gym/text.inc').read_text(errors='replace')
        symbols = set(re.findall(r'^([A-Za-z_]\w*)::', source, re.MULTILINE))
        self.assertEqual(23, len(symbols))
        self.assertTrue(symbols.issubset(templates))

    def test_mauville_houses_and_services_are_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        symbols = set()
        areas = ('MauvilleCity_House1', 'MauvilleCity_House2', 'MauvilleCity_Mart',
                 'MauvilleCity_PokemonCenter_1F')
        for area in areas:
            source = (demo.ROOT / f'data/maps/{area}/text.inc').read_text(errors='replace')
            symbols.update(re.findall(r'^([A-Za-z_]\w*)::', source, re.MULTILINE))
        self.assertEqual(13, len(symbols))
        self.assertTrue(symbols.issubset(templates))

    def test_mauville_bike_shop_and_game_corner_are_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        symbols = set()
        for area in ('MauvilleCity_BikeShop', 'MauvilleCity_GameCorner'):
            source = (demo.ROOT / f'data/maps/{area}/text.inc').read_text(errors='replace')
            symbols.update(re.findall(r'^([A-Za-z_]\w*)::', source, re.MULTILINE))
        self.assertEqual(55, len(symbols))
        self.assertTrue(symbols.issubset(templates))

    def test_routes_111_and_112_are_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        symbols = set()
        areas = ('Route111', 'Route111_OldLadysRestStop',
                 'Route111_WinstrateFamilysHouse', 'Route112',
                 'Route112_CableCarStation')
        for area in areas:
            source = (demo.ROOT / f'data/maps/{area}/text.inc').read_text(errors='replace')
            symbols.update(re.findall(r'^([A-Za-z_]\w*)::', source, re.MULTILINE))
        self.assertEqual(45, len(symbols))
        self.assertTrue(symbols.issubset(templates))

    def test_verdanturf_and_rusturf_tunnel_are_bilingual(self):
        templates = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        symbols = set()
        areas = ('VerdanturfTown', 'VerdanturfTown_House',
                 'VerdanturfTown_WandasHouse',
                 'VerdanturfTown_FriendshipRatersHouse', 'VerdanturfTown_Mart',
                 'VerdanturfTown_PokemonCenter_1F', 'VerdanturfTown_ContestLobby',
                 'VerdanturfTown_ContestHall', 'RusturfTunnel')
        for area in areas:
            source = (demo.ROOT / f'data/maps/{area}/text.inc').read_text(errors='replace')
            symbols.update(re.findall(r'^([A-Za-z_]\w*)::', source, re.MULTILINE))
        self.assertEqual(62, len(symbols))
        self.assertTrue(symbols.issubset(templates))

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
