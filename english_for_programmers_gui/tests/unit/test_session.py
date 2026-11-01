# Занятие (core/session.py, класс Session): порция слов и счёт ответов.

import unittest

from core.session import (
    CARDS,
    CHOICE,
    EXCELLENT,
    GOOD,
    KEEP_GOING,
    STUDY_MODES,
    TYPING,
    Session,
)


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


class RecordAnswerTests(unittest.TestCase):
    """Сессия сама ведёт свой счёт: Lesson не меняет её поля напрямую."""

    def test_right_answer_increases_right_and_moves_on(self):
        session = Session("cards", "Тема", ["a", "b"])

        session.record_answer(True)

        self.assertEqual((session.right, session.wrong, session.index), (1, 0, 1))

    def test_wrong_answer_increases_wrong_and_moves_on(self):
        session = Session("cards", "Тема", ["a", "b"])

        session.record_answer(False)

        self.assertEqual((session.right, session.wrong, session.index), (0, 1, 1))

    def test_wrong_answer_remembers_word_for_retry(self):
        session = Session("cards", "Тема", ["a", "b"])

        session.record_answer(False)

        self.assertEqual(session.mistakes, ["a"])

    def test_answer_after_last_word_is_an_error(self):
        """Ответить на занятие, которое уже кончилось, - ошибка в программе."""
        session = Session("cards", "Тема", ["a"], index=1)

        with self.assertRaises(ValueError):
            session.record_answer(True)

    def test_skipped_word_is_not_counted_as_answer(self):
        """Пропуск - для слов, которые удалили из словаря: ответа на них нет."""
        session = Session("cards", "Тема", ["removed", "b"])

        session.skip_word()

        self.assertEqual((session.index, session.answered), (1, 0))

    def test_current_key_is_word_at_current_place(self):
        session = Session("cards", "Тема", ["a", "b"], index=1)

        self.assertEqual(session.current_key, "b")

    def test_finished_session_has_no_current_key(self):
        self.assertIsNone(Session("cards", "Тема", ["a"], index=1).current_key)


class RatingTests(unittest.TestCase):
    """Оценка за занятие на экране итогов. Пороги: 100% и 70%."""

    def rating(self, right: int, wrong: int) -> str:
        keys = ["w"] * (right + wrong)
        return Session("cards", "Тема", keys, right=right, wrong=wrong).rating

    def test_all_right_is_excellent(self):
        self.assertEqual(self.rating(10, 0), EXCELLENT)

    def test_seventy_percent_is_good(self):
        self.assertEqual(self.rating(7, 3), GOOD)

    def test_below_seventy_percent_means_keep_going(self):
        self.assertEqual(self.rating(6, 4), KEEP_GOING)


class ModeConstantsTests(unittest.TestCase):
    def test_study_modes_are_listed_in_menu_order(self):
        self.assertEqual(STUDY_MODES, (CARDS, CHOICE, TYPING))

    def test_mode_names_match_saved_sessions_of_old_versions(self):
        """Эти строки уже записаны в state.json у пользователя: менять их нельзя."""
        self.assertEqual((CARDS, CHOICE, TYPING), ("cards", "choice", "typing"))


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
