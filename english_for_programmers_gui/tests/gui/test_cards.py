# Страница "Карточки": слово, по пробелу перевод, затем "знаю" или "не знаю".

import unittest

from core.lesson import WEAK_WORDS
from tests.gui.base import GuiTestCase

N_KEY = 78  # Ctrl+N - новое занятие (в русской раскладке клавиша "т")


class CardsTestCase(GuiTestCase):
    def setUp(self):
        super().setUp()
        self.page = self.open_page("cards")

    def start_lesson(self) -> None:
        self.press("т", N_KEY, ctrl=True)


class StartTests(CardsTestCase):
    def test_page_waits_for_start_before_first_lesson(self):
        self.assertIs(self.visible_screen(self.page), self.page.intro)

    def test_ctrl_n_starts_lesson_from_first_word(self):
        self.start_lesson()

        self.assertIs(self.visible_screen(self.page), self.page.body)
        self.assertEqual(self.page.session.index, 0)

    def test_weak_words_lesson_without_weak_words_explains_why_it_did_not_start(self):
        self.page.topic_menu.set(WEAK_WORDS)

        self.page.start_new()

        self.assertIs(self.visible_screen(self.page), self.page.intro)
        self.assertIn("Слабых слов", self.page.intro_label.cget("text"))

    def test_ctrl_down_chooses_next_topic(self):
        before = self.page.topic_menu.get()

        self.press("Down", 40, ctrl=True)

        self.assertNotEqual(self.page.topic_menu.get(), before)


class AnswerTests(CardsTestCase):
    def setUp(self):
        super().setUp()
        self.start_lesson()

    def test_answer_is_not_accepted_before_translation_is_shown(self):
        """Сначала надо вспомнить перевод и посмотреть его, потом отвечать."""
        self.press("2")

        self.assertEqual(self.page.session.index, 0)

    def test_space_shows_translation(self):
        word = self.page.word

        self.press("space")

        self.assertTrue(self.page.revealed)
        self.assertEqual(self.page.ru_label.cget("text"), word.ru)

    def test_key_2_means_i_know_and_shows_next_word(self):
        first = self.page.word
        self.press("space")

        self.press("2")

        self.assertEqual(self.page.session.right, 1)
        self.assertNotEqual(self.page.word, first)

    def test_key_1_means_i_do_not_know(self):
        self.press("space")

        self.press("1")

        self.assertEqual(self.page.session.wrong, 1)

    def test_place_is_saved_after_answer(self):
        self.press("space")

        self.press("2")

        self.assertEqual(self.app.settings.session("cards").index, 1)


if __name__ == "__main__":
    unittest.main()
