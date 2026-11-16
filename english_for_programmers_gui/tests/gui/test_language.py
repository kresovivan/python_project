# Язык обучения в окне: переключатель English / 中文 и Ctrl+L.
#
# Главное правило: у каждого языка свои слова, свой прогресс и свои
# страницы "Азбука" (у китайского - "Звуки и тоны") и "Грамматика".

import unittest

from core import grammar, grammar_zh, pinyin
from core.answers import PinyinChecker
from core.settings import Settings
from tests.gui.base import GuiTestCase

L_KEY = 76  # Ctrl+L; в русской раскладке это клавиша "д"


class SwitchTests(GuiTestCase):
    def test_program_starts_in_english(self):
        self.assertEqual(self.app.language.code, "en")
        self.assertIs(self.app.pages["grammar"].topics, grammar.TOPICS)

    def test_ctrl_l_switches_to_chinese_in_russian_layout(self):
        self.press("д", L_KEY, ctrl=True)

        self.assertEqual(self.app.language.code, "zh")

    def test_ctrl_l_twice_returns_to_english(self):
        self.press("д", L_KEY, ctrl=True)
        self.press("д", L_KEY, ctrl=True)

        self.assertEqual(self.app.language.code, "en")

    def test_switch_in_menu_changes_language(self):
        """Щелчок по "中文" на переключателе в меню."""
        self.app.sidebar.language_switch._command("中文")

        self.assertEqual(self.app.language.code, "zh")

    def test_switching_back_and_forth_leaves_no_old_screens(self):
        """После переключений в окне одно меню и один держатель страниц, без
        остатков старого экрана и без "шторки", которая закрывает перестройку."""
        for code in ("zh", "en", "zh"):
            self.app.switch_language(code)

        shown = [
            type(child).__name__
            for child in self.app.winfo_children()
            # размещён в окне, значит виден; сообщение "Язык: ..." (Toast) не в счёт
            if child.winfo_manager() and child is not self.app.toast
        ]
        self.assertEqual(sorted(shown), ["PageHost", "Sidebar"])

    def test_after_switch_program_shows_home_page(self):
        self.open_page("grammar")

        self.app.switch_language("zh")

        self.assertEqual(self.app.current.key, "home")

    def test_chosen_language_is_remembered_after_restart(self):
        self.app.switch_language("zh")
        self.app.on_close()

        app = self.open_app()

        self.assertEqual(app.language.code, "zh")


class ChinesePagesTests(GuiTestCase):
    def setUp(self):
        super().setUp()
        self.app.switch_language("zh")

    def test_chinese_words_are_loaded(self):
        self.assertTrue(self.app.vocabulary.get("电脑"))

    def test_sounds_and_tones_page_replaces_alphabet(self):
        page = self.app.pages["alphabet"]

        self.assertEqual(page.title, "Звуки и тоны")
        self.assertIs(page.topics, pinyin.TOPICS)

    def test_grammar_page_shows_chinese_grammar(self):
        self.assertIs(self.app.pages["grammar"].topics, grammar_zh.TOPICS)

    def test_voice_list_has_chinese_voices(self):
        self.assertTrue(self.app.voice.voice.startswith("zh-CN"))

    def test_typing_page_checks_pinyin(self):
        page = self.open_page("typing")
        page.start_new()
        answer = PinyinChecker.expected(page.word)

        page.entry.insert(0, answer)
        self.press("Return")

        self.assertEqual(page.session.right, 1)

    def test_dictionary_finds_word_by_pinyin(self):
        found = self.app.vocabulary.search("diannao")

        self.assertIn("电脑", [word.en for word in found])


class SeparateProgressTests(GuiTestCase):
    def test_chinese_answers_do_not_change_english_progress(self):
        self.app.switch_language("zh")
        page = self.open_page("cards")
        page.start_new()

        page.answer(True)

        english = (self.user_data / "progress.json").exists()
        chinese = (self.user_data / "zh" / "progress.json").exists()
        self.assertFalse(english)
        self.assertTrue(chinese)

    def test_english_lesson_is_waiting_after_chinese(self):
        """Начатое английское занятие не пропадает, пока учим китайский."""
        cards = self.open_page("cards")
        cards.start_new()
        cards.answer(True)

        self.app.switch_language("zh")
        self.app.switch_language("en")

        saved = Settings(self.user_data / "state.json").session("cards")
        self.assertEqual(saved.index, 1)


if __name__ == "__main__":
    unittest.main()
