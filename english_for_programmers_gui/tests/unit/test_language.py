# Язык обучения (core/language.py): чем английский отличается от китайского.

import unittest
from pathlib import Path

from core.answers import AnswerChecker, PinyinChecker
from core.language import CHINESE, ENGLISH, LANGUAGES, find_language
from core.vocabulary import Vocabulary
from tests.support import ROOT


class FindLanguageTests(unittest.TestCase):
    def test_language_is_found_by_code(self):
        self.assertIs(find_language("zh"), CHINESE)

    def test_unknown_code_gives_english(self):
        """В настройках мог остаться неизвестный код - тогда английский."""
        self.assertIs(find_language("xx"), ENGLISH)
        self.assertIs(find_language(None), ENGLISH)


class FoldersTests(unittest.TestCase):
    def test_english_progress_stays_in_user_data(self):
        """Прогресс английского и раньше лежал прямо в user_data - не теряем его."""
        user_data = Path("user_data")

        self.assertEqual(ENGLISH.user_dir(user_data), user_data)

    def test_chinese_progress_is_kept_separately(self):
        user_data = Path("user_data")

        self.assertEqual(CHINESE.user_dir(user_data), user_data / "zh")

    def test_every_language_has_words(self):
        for language in LANGUAGES.values():
            with self.subTest(language=language.code):
                vocabulary = Vocabulary.from_folder(language.data_dir(ROOT))

                self.assertGreater(len(vocabulary), 0)


class RulesTests(unittest.TestCase):
    def test_english_word_is_typed_as_it_is(self):
        self.assertIs(ENGLISH.checker, AnswerChecker)

    def test_chinese_word_is_typed_in_pinyin(self):
        self.assertIs(CHINESE.checker, PinyinChecker)

    def test_only_chinese_is_searched_by_pronunciation(self):
        self.assertFalse(ENGLISH.searches_sound)
        self.assertTrue(CHINESE.searches_sound)

    def test_default_voice_is_in_the_voice_list(self):
        for language in LANGUAGES.values():
            with self.subTest(language=language.code):
                codes = [code for code, _ in language.voices]

                self.assertIn(language.default_voice, codes)

    def test_chinese_has_its_own_sounds_page(self):
        """У английского - азбука с картинками, у китайского - "Звуки и тоны"."""
        self.assertFalse(ENGLISH.sounds)
        self.assertTrue(CHINESE.sounds)


if __name__ == "__main__":
    unittest.main()
