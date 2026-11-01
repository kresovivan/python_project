# Проверка ответа и подсказка в "Написании слова" (core/answers.py).
#
# Правило проверки: регистр, знаки препинания, апострофы и лишние пробелы
# не важны, важны только буквы и порядок слов.

import unittest

from core.answers import AnswerChecker
from core.models import Word


def word(en: str) -> Word:
    """Слово для теста: перевод и тема здесь не важны."""
    return Word(en, "перевод", "", "Тест")


class IsCorrectTests(unittest.TestCase):
    def test_exact_answer_is_correct(self):
        self.assertTrue(AnswerChecker.is_correct("loop", word("loop")))

    def test_letter_case_is_ignored(self):
        self.assertTrue(AnswerChecker.is_correct("LoOp", word("loop")))

    def test_punctuation_is_ignored(self):
        self.assertTrue(AnswerChecker.is_correct("it works", word("It works!")))

    def test_straight_and_typographic_apostrophes_are_ignored(self):
        """Апостроф можно не ставить или поставить любой: ' или ’."""
        target = word("don't")

        for typed in ("dont", "don't", "don’t"):
            with self.subTest(typed=typed):
                self.assertTrue(AnswerChecker.is_correct(typed, target))

    def test_extra_spaces_are_ignored(self):
        self.assertTrue(AnswerChecker.is_correct("  it   works  ", word("it works")))

    def test_note_in_brackets_is_not_required(self):
        self.assertTrue(AnswerChecker.is_correct("commit", word("commit (DB)")))

    def test_different_word_is_wrong(self):
        self.assertFalse(
            AnswerChecker.is_correct("it does work", word("It doesn't work!"))
        )

    def test_missing_word_is_wrong(self):
        self.assertFalse(AnswerChecker.is_correct("pull", word("pull request")))


class HintTests(unittest.TestCase):
    """Подсказка: первая буква видна, остальные буквы заменены прочерками."""

    def test_hint_shows_first_letter_and_hides_the_rest(self):
        self.assertEqual(AnswerChecker.hint("loop"), "l _ _ _")

    def test_hint_shows_gap_between_words_as_wide_space(self):
        self.assertEqual(AnswerChecker.hint("Can you"), "C _ _    _ _ _")

    def test_hint_shows_apostrophe(self):
        self.assertEqual(AnswerChecker.hint("don't"), "d _ _ ' _")


if __name__ == "__main__":
    unittest.main()
