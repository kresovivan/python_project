# Вопрос для "Выбора перевода" (core/questions.py, класс ChoiceQuestion).
#
# Раньше варианты ответа собирала страница окна (ChoicePage.render), и
# проверить это правило можно было только медленным тестом с окном.

import tempfile
import unittest
from pathlib import Path

from core.questions import ChoiceQuestion
from tests.support import use_fixed_random, write_vocabulary


class ChoiceQuestionTests(unittest.TestCase):
    def setUp(self):
        use_fixed_random(self)
        tmp = tempfile.TemporaryDirectory(prefix="efp_question_")
        self.addCleanup(tmp.cleanup)
        self.vocabulary = write_vocabulary(
            Path(tmp.name),
            """
            loop|цикл|луп
            break|прервать|брейк
            continue|продолжить|континью
            while|пока|вайл
            for|для|фо
            """,
        )
        self.word = self.vocabulary.get("loop")

    def test_question_has_four_options_by_default(self):
        question = ChoiceQuestion.create(self.word, self.vocabulary)

        self.assertEqual(len(question.options), 4)

    def test_number_of_options_can_be_changed(self):
        question = ChoiceQuestion.create(self.word, self.vocabulary, size=3)

        self.assertEqual(len(question.options), 3)

    def test_correct_translation_is_among_options_once(self):
        question = ChoiceQuestion.create(self.word, self.vocabulary)

        self.assertEqual(question.options.count("цикл"), 1)

    def test_correct_index_points_to_translation(self):
        question = ChoiceQuestion.create(self.word, self.vocabulary)

        self.assertEqual(question.options[question.correct_index], "цикл")

    def test_choosing_correct_option_is_right(self):
        question = ChoiceQuestion.create(self.word, self.vocabulary)

        self.assertTrue(question.is_correct(question.correct_index))

    def test_choosing_other_option_is_wrong(self):
        question = ChoiceQuestion.create(self.word, self.vocabulary)
        wrong = (question.correct_index + 1) % len(question.options)

        self.assertFalse(question.is_correct(wrong))

    def test_correct_option_is_not_always_in_same_place(self):
        """Иначе ответ можно угадать по месту, не читая варианты."""
        places = {
            ChoiceQuestion.create(self.word, self.vocabulary).correct_index
            for _ in range(40)
        }

        self.assertGreater(len(places), 1)

    def test_question_cannot_be_changed_after_creation(self):
        question = ChoiceQuestion.create(self.word, self.vocabulary)

        with self.assertRaises(AttributeError):
            question.options.append("лишний вариант")  # options - кортеж


if __name__ == "__main__":
    unittest.main()
