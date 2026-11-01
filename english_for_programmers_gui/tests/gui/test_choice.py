# Страница "Выбор перевода": английское слово и четыре варианта перевода.

import unittest
from unittest.mock import patch

from gui.pages.study import ChoicePage
from tests.gui.base import GuiTestCase
from tests.support import pump, use_fixed_random


class ChoiceTestCase(GuiTestCase):
    def setUp(self):
        super().setUp()
        use_fixed_random(self)
        self.page = self.open_page("choice")
        self.page.start_new()

    def correct_index(self) -> int:
        return self.page.options.index(self.page.word.ru)

    def wrong_index(self) -> int:
        return next(
            i
            for i, option in enumerate(self.page.options)
            if option != self.page.word.ru
        )


class OptionsTests(ChoiceTestCase):
    def test_there_are_four_options(self):
        self.assertEqual(len(self.page.options), ChoicePage.OPTIONS)

    def test_exactly_one_option_is_correct(self):
        self.assertEqual(self.page.options.count(self.page.word.ru), 1)

    def test_options_are_all_different(self):
        """Та же ошибка с синонимами, но проверенная уже на экране."""
        self.assertEqual(len(set(self.page.options)), len(self.page.options))


class WrongChoiceTests(ChoiceTestCase):
    def test_wrong_choice_is_counted_as_mistake(self):
        self.page.choose(self.wrong_index())

        self.assertEqual(self.page.session.wrong, 1)

    def test_buttons_are_locked_after_choice(self):
        self.page.choose(self.wrong_index())

        states = {str(button.cget("state")) for button in self.page.option_buttons}

        self.assertEqual(states, {"disabled"})

    def test_second_choice_for_same_word_is_ignored(self):
        self.page.choose(self.wrong_index())

        self.page.choose(self.correct_index())

        self.assertEqual(self.page.session.answered, 1)

    def test_word_stays_on_screen_after_mistake_until_enter(self):
        """После ошибки даём время рассмотреть правильный ответ."""
        word = self.page.word
        self.page.choose(self.wrong_index())
        pump(self.app, 0.1)
        self.assertEqual(self.page.word, word)

        self.press("Return")

        self.assertNotEqual(self.page.word, word)


class RightChoiceTests(ChoiceTestCase):
    def test_right_choice_is_counted(self):
        self.page.choose(self.correct_index())

        self.assertEqual(self.page.session.right, 1)

    def test_next_word_appears_by_itself_after_right_choice(self):
        word = self.page.word

        # Пауза перед следующим словом в программе 0.9 с. В тесте ставим 0,
        # чтобы не ждать: проверяем сам переход, а не длину паузы.
        with patch.object(ChoicePage, "AUTO_NEXT_MS", 0):
            self.page.choose(self.correct_index())
        pump(self.app, 0.05)

        self.assertNotEqual(self.page.word, word)

    def test_digit_key_chooses_option(self):
        self.press(str(self.correct_index() + 1))

        self.assertEqual(self.page.session.right, 1)


if __name__ == "__main__":
    unittest.main()
