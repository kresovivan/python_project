# Занятие (core/session.py, класс Session): порция слов и счёт ответов.

import unittest

from core.session import Session


class NewSessionTests(unittest.TestCase):
    def test_new_session_starts_from_first_word(self):
        session = Session("cards", "Тема", ["a", "b", "c"])

        self.assertEqual(session.index, 0)
        self.assertEqual(session.answered, 0)
        self.assertFalse(session.finished)

    def test_total_is_number_of_words(self):
        session = Session("cards", "Тема", ["a", "b", "c"])

        self.assertEqual(session.total, 3)

    def test_each_session_has_its_own_mistakes_list(self):
        """Список ошибок не должен быть общим для разных занятий (тема про ссылки)."""
        first = Session("cards", "Тема", ["a"])
        second = Session("cards", "Тема", ["a"])

        first.mistakes.append("a")

        self.assertEqual(second.mistakes, [])


class ScoreTests(unittest.TestCase):
    def test_answered_is_right_plus_wrong(self):
        session = Session("cards", "Тема", ["a", "b", "c"], right=2, wrong=1)

        self.assertEqual(session.answered, 3)

    def test_percent_is_share_of_right_answers_rounded(self):
        session = Session("cards", "Тема", ["a", "b", "c"], right=2, wrong=1)

        self.assertEqual(session.percent, 67)  # 2 из 3 = 66.7%, округляем

    def test_percent_is_zero_before_first_answer(self):
        """Деления на ноль быть не должно."""
        session = Session("cards", "Тема", ["a"])

        self.assertEqual(session.percent, 0)

    def test_fraction_is_share_of_passed_words(self):
        session = Session("cards", "Тема", ["a", "b", "c", "d"], index=1)

        self.assertEqual(session.fraction, 0.25)

    def test_fraction_of_empty_session_is_zero(self):
        self.assertEqual(Session("cards", "Тема", []).fraction, 0.0)

    def test_session_is_finished_after_last_word(self):
        session = Session("cards", "Тема", ["a", "b"], index=2)

        self.assertTrue(session.finished)


class SerializationTests(unittest.TestCase):
    def test_session_survives_saving_to_dict_and_back(self):
        """to_dict нужен для записи в JSON, from_dict - для чтения обратно."""
        session = Session(
            "typing", "Тема", ["a", "b"], index=1, right=1, mistakes=["b"]
        )

        restored = Session.from_dict(session.to_dict())

        self.assertEqual(restored, session)


if __name__ == "__main__":
    unittest.main()
