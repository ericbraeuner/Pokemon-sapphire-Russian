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
        self.assertGreaterEqual(len(moves), 137)
        for move in ('MOVE_CUT', 'MOVE_FLY', 'MOVE_HEADBUTT', 'MOVE_DISABLE',
                     'MOVE_SURF', 'MOVE_ICE_BEAM', 'MOVE_EARTHQUAKE',
                     'MOVE_PSYCHIC', 'MOVE_HYPNOSIS', 'MOVE_RECOVER',
                     'MOVE_LIGHT_SCREEN', 'MOVE_SELF_DESTRUCT'):
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
        self.assertNotIn('Learner_', item)
        entries = validate.load(demo.ROOT / 'language_learning/ui.json')
        for key in ('Potion', 'Antidote', 'ParaHeal', 'Awakening', 'PokeBall'):
            for tag, mapping, glyphs in [('ru', self.russian, self.glyphs), ('de', self.latin, {})]:
                self.assertEqual(1, len(demo.wrap(entries[key][tag], mapping, glyphs, 88)))

    def test_shared_item_messages_preserve_runtime_fields(self):
        entries = validate.load(demo.ROOT / 'language_learning/field_templates.json')
        expected = {'Text_ObtainedTheItem': [3], 'Text_FoundOneItem': [1, 3],
                    'Text_PutItemInPocket': [3, 4], 'gOtherText_SoldItem': [2, 3],
                    'gOtherText_Coins3': [2], 'gOtherText_ContainsMove': [2],
                    'gOtherText_SnapConfusion': [2], 'gOtherText_SafariStock': [2]}
        exports = (demo.ROOT / 'data/text/obtain_item.inc').read_text()
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

    def test_shared_item_names_and_descriptions_fit(self):
        import re
        code = (demo.ROOT / 'src/shop.c').read_text()
        names = re.findall(r'case ITEM_\w+: return description \? LEARNER_UI\(Learner_GetLanguage\(\), (\w+)\) : LEARNER_UI\(Learner_GetLanguage\(\), (\w+)\)', code)
        self.assertEqual(len(names), 47)
        entries = validate.load(demo.ROOT / 'language_learning/ui.json')
        for description, name in names:
            for tag, mapping, glyphs in [('ru', self.russian, self.glyphs), ('de', self.latin, {})]:
                self.assertEqual(len(demo.wrap(entries[name][tag], mapping, glyphs, 88)), 1)
                self.assertLessEqual(len(demo.wrap(entries[description][tag], mapping, glyphs, 104)), 2)

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
