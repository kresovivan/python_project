# Азбука (core/alphabet.py): 26 букв, у каждой название, звук, слово и картинка.

import string
import unittest

from core.alphabet import ALPHABET, find_letter
from tests.support import ROOT

PICTURES = ROOT / "assets" / "alphabet"


class AlphabetContentTests(unittest.TestCase):
    def test_all_26_letters_in_order(self):
        self.assertEqual(
            [letter.upper for letter in ALPHABET], list(string.ascii_uppercase)
        )

    def test_small_letter_matches_big_one(self):
        wrong = [
            letter.upper for letter in ALPHABET if letter.lower != letter.upper.lower()
        ]

        self.assertEqual(wrong, [])

    def test_example_word_contains_its_letter(self):
        """Обычно слово начинается с буквы. У X - заканчивается: fox."""
        wrong = [
            (letter.upper, letter.word)
            for letter in ALPHABET
            if letter.lower not in letter.word.lower()
        ]

        self.assertEqual(wrong, [])

    def test_every_letter_has_name_sound_and_translation(self):
        empty = [
            letter.upper
            for letter in ALPHABET
            if not (
                letter.name_ru
                and letter.sound_ru
                and letter.word_sound
                and letter.word_ru
            )
        ]

        self.assertEqual(empty, [])

    def test_every_picture_file_exists(self):
        missing = [
            letter.picture
            for letter in ALPHABET
            if not (PICTURES / letter.picture).exists()
        ]

        self.assertEqual(missing, [])


class FindLetterTests(unittest.TestCase):
    def test_letter_is_found_by_small_or_big_symbol(self):
        self.assertEqual(find_letter("c").upper, "C")
        self.assertEqual(find_letter("C").upper, "C")

    def test_not_a_letter_gives_none(self):
        self.assertIsNone(find_letter("1"))


class SpeechTests(unittest.TestCase):
    def test_letter_and_word_are_spoken_together(self):
        """По клавише P звучит буква, а потом слово: "A. Ant."."""
        letter = find_letter("A")

        self.assertEqual(letter.speech, "A. Ant.")


if __name__ == "__main__":
    unittest.main()
