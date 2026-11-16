# Страница "Азбука" (gui/pages/alphabet.py): буква, звук, слово, картинка.

import unittest

from core.alphabet import ALPHABET
from tests.gui.base import GuiTestCase

C_KEY, P_KEY = 67, 80  # номера физических клавиш C и P


class AlphabetTestCase(GuiTestCase):
    def setUp(self):
        super().setUp()
        self.page = self.open_page("alphabet")


class ShowLetterTests(AlphabetTestCase):
    def test_first_visit_starts_with_letter_a(self):
        self.assertEqual(self.page.letter.upper, "A")

    def test_letter_word_and_translation_are_shown(self):
        self.assertEqual(self.page.big_letter.cget("text"), "Aa")
        self.assertIn("Ant", self.page.word_label.cget("text"))
        self.assertIn("муравей", self.page.translation_label.cget("text"))

    def test_picture_is_shown(self):
        self.assertTrue(self.page.picture_label.cget("image"))


class ChooseLetterTests(AlphabetTestCase):
    def test_right_arrow_shows_next_letter(self):
        self.press("Right")

        self.assertEqual(self.page.letter.upper, "B")

    def test_left_arrow_from_a_shows_z(self):
        self.press("Left")

        self.assertEqual(self.page.letter.upper, "Z")

    def test_letter_key_opens_that_letter_in_russian_layout(self):
        """Клавиша C в русской раскладке даёт "с", но открыть надо букву C."""
        self.press("с", C_KEY)

        self.assertEqual(self.page.letter.upper, "C")

    def test_click_on_letter_tile_opens_that_letter(self):
        self.page.letter_buttons["Z"].invoke()

        self.assertEqual(self.page.letter.upper, "Z")

    def test_chosen_letter_is_remembered(self):
        self.press("Right")

        self.assertEqual(self.app.settings.get("alphabet_index"), 1)


class SpeakTests(AlphabetTestCase):
    def test_p_speaks_letter_and_word(self):
        self.press("з", P_KEY)

        self.assertEqual(self.spoken[-1], (ALPHABET[0].speech, False))


if __name__ == "__main__":
    unittest.main()
