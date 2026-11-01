# Переходы между страницами, справка F1, смена темы оформления.
#
# Буквы в сочетаниях передаются в русской раскладке ("е" вместо T):
# программа обязана узнавать клавишу по её номеру (keycode), а не по букве.

import unittest

import customtkinter as ctk

from gui.app import PAGE_CLASSES
from tests.gui.base import GuiTestCase

T_KEY, F_KEY = 84, 70  # номера физических клавиш T и F


class StartTests(GuiTestCase):
    def test_program_opens_on_home_page(self):
        self.assertEqual(self.app.current.key, "home")

    def test_only_one_page_is_visible(self):
        visible = [page for page in self.app.pages.values() if page.winfo_ismapped()]

        self.assertEqual(len(visible), 1)

    def test_menu_has_every_page(self):
        self.assertEqual(len(self.app.host.keys), len(PAGE_CLASSES))


class PageHotkeyTests(GuiTestCase):
    def test_ctrl_and_number_opens_page_with_that_number(self):
        for number, key in enumerate(self.app.host.keys, start=1):
            with self.subTest(number=number):
                self.press(str(number), 48 + number, ctrl=True)

                self.assertEqual(self.app.current.key, key)

    def test_ctrl_tab_opens_next_page(self):
        self.press("Tab", 9, ctrl=True)

        self.assertEqual(self.app.current.key, self.app.host.keys[1])

    def test_ctrl_shift_tab_from_first_page_opens_last_page(self):
        self.press("ISO_Left_Tab", 9, ctrl=True, shift=True)

        self.assertEqual(self.app.current.key, self.app.host.keys[-1])

    def test_ctrl_f_opens_dictionary_in_russian_layout(self):
        self.press("а", F_KEY, ctrl=True)

        self.assertEqual(self.app.current.key, "dictionary")

    def test_escape_returns_to_home_page(self):
        self.open_page("stats")

        self.press("Escape")

        self.assertEqual(self.app.current.key, "home")

    def test_number_on_home_page_starts_exercise(self):
        """На главной 1-4 - быстрый старт: карточки, выбор, написание, ошибки."""
        for digit, key in enumerate(("cards", "choice", "typing", "errors"), start=1):
            with self.subTest(digit=digit):
                self.open_page("home")

                self.press(str(digit))

                self.assertEqual(self.app.current.key, key)


class HelpTests(GuiTestCase):
    def test_f1_shows_help(self):
        self.press("F1")

        self.assertTrue(self.app.help.visible)

    def test_escape_hides_help(self):
        self.press("F1")

        self.press("Escape")

        self.assertFalse(self.app.help.visible)

    def test_other_keys_do_nothing_while_help_is_open(self):
        self.press("F1")

        self.press("2", 50, ctrl=True)

        self.assertEqual(self.app.current.key, "home")
        self.assertTrue(self.app.help.visible)


class ThemeTests(GuiTestCase):
    def test_ctrl_t_switches_theme_in_russian_layout(self):
        before = ctk.get_appearance_mode()

        self.press("е", T_KEY, ctrl=True)

        self.assertNotEqual(ctk.get_appearance_mode(), before)

    def test_second_ctrl_t_returns_previous_theme(self):
        before = ctk.get_appearance_mode()

        self.press("е", T_KEY, ctrl=True)
        self.press("е", T_KEY, ctrl=True)

        self.assertEqual(ctk.get_appearance_mode(), before)


if __name__ == "__main__":
    unittest.main()
