# Прогресс (core/progress.py): статусы слов, история по дням, серия дней,
# подбор слов для занятия. Файл progress.json - во временной папке.

import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from core.models import Word
from core.progress import LEARNED, LEARNING, NEW, WEAK, Progress
from tests.support import use_fixed_random

LOOP = Word("loop", "цикл", "луп", "Циклы")


def make_words(count: int) -> list[Word]:
    return [Word(f"word{i}", f"слово{i}", "", "Тест") for i in range(count)]


class ProgressTestCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="efp_progress_")
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name) / "progress.json"
        self.progress = Progress(self.path)

    def answer(self, word: Word, *results: bool) -> None:
        """Записать несколько ответов подряд: answer(LOOP, False, True)."""
        for is_right in results:
            self.progress.record(word, is_right)

    def write_days(self, *days_ago: int) -> None:
        """Записать в файл занятия N дней назад (0 - сегодня, 1 - вчера)."""
        days = {}
        for ago in days_ago:
            day = (date.today() - timedelta(days=ago)).isoformat()
            days[day] = {"right": 1, "wrong": 0}
        self.path.write_text(json.dumps({"days": days}), encoding="utf-8")


class StatusTests(ProgressTestCase):
    """Статус слова: новое, слабое, изучаю, выучено."""

    def test_word_without_answers_is_new(self):
        self.assertEqual(self.progress.status(LOOP), NEW)

    def test_wrong_answer_makes_word_weak(self):
        self.answer(LOOP, False)

        self.assertEqual(self.progress.status(LOOP), WEAK)

    def test_word_stays_weak_while_mistakes_are_not_fewer_than_right_answers(self):
        self.answer(LOOP, False, True)

        self.assertEqual(self.progress.status(LOOP), WEAK)

    def test_right_answer_makes_word_learning(self):
        self.answer(LOOP, True)

        self.assertEqual(self.progress.status(LOOP), LEARNING)

    def test_word_is_learned_after_enough_right_answers(self):
        self.answer(LOOP, *[True] * Progress.LEARNED_AFTER)

        self.assertEqual(self.progress.status(LOOP), LEARNED)

    def test_counts_groups_words_by_status(self):
        weak, learning, new = make_words(3)
        self.answer(weak, False)
        self.answer(learning, True)

        counts = self.progress.counts([weak, learning, new])

        self.assertEqual(counts, {NEW: 1, WEAK: 1, LEARNING: 1, LEARNED: 0})


class SavingTests(ProgressTestCase):
    def test_answers_are_kept_after_restart(self):
        self.answer(LOOP, False)

        self.assertEqual(Progress(self.path).status(LOOP), WEAK)

    def test_reset_forgets_all_answers(self):
        self.answer(LOOP, True)

        self.progress.reset()

        self.assertEqual(Progress(self.path).status(LOOP), NEW)
        self.assertEqual(Progress(self.path).today_total(), 0)

    def test_broken_file_starts_empty_progress(self):
        self.path.write_text("{bad json", encoding="utf-8")

        self.assertEqual(Progress(self.path).status(LOOP), NEW)


class HistoryTests(ProgressTestCase):
    def test_today_total_counts_right_and_wrong_answers(self):
        self.answer(LOOP, True, False, True)

        self.assertEqual(self.progress.today_total(), 3)

    def test_history_has_requested_number_of_days_ending_today(self):
        history = self.progress.history(14)

        self.assertEqual(len(history), 14)
        self.assertEqual(history[0][0], date.today() - timedelta(days=13))
        self.assertEqual(history[-1][0], date.today())

    def test_history_shows_todays_right_and_wrong_answers(self):
        self.answer(LOOP, True, True, False)

        _, right, wrong = self.progress.history(14)[-1]

        self.assertEqual((right, wrong), (2, 1))


class StreakTests(ProgressTestCase):
    """Серия - сколько дней подряд были занятия."""

    def test_no_lessons_means_no_streak(self):
        self.assertEqual(self.progress.streak(), 0)

    def test_lesson_today_is_streak_of_one(self):
        self.write_days(0)

        self.assertEqual(Progress(self.path).streak(), 1)

    def test_streak_is_not_lost_before_todays_lesson(self):
        """Утром, пока сегодня ещё не занимались, вчерашняя серия сохраняется."""
        self.write_days(1, 2)

        self.assertEqual(Progress(self.path).streak(), 2)

    def test_missed_day_breaks_streak(self):
        self.write_days(0, 2)

        self.assertEqual(Progress(self.path).streak(), 1)


class PickTests(ProgressTestCase):
    """Подбор слов для занятия: сначала слабые, потом новые, выученные в конце."""

    def setUp(self):
        super().setUp()
        use_fixed_random(self)

    def test_pick_returns_requested_number_of_words(self):
        self.assertEqual(len(self.progress.pick(make_words(10), 4)), 4)

    def test_pick_returns_all_words_when_there_are_fewer_than_requested(self):
        words = make_words(3)

        self.assertCountEqual(self.progress.pick(words, 20), words)

    def test_weak_words_are_picked_first(self):
        words = make_words(6)
        weak = words[4:]
        for word in weak:
            self.answer(word, False)

        picked = self.progress.pick(words, 2)

        self.assertCountEqual(picked, weak)

    def test_learned_words_are_picked_last(self):
        words = make_words(4)
        learned = words[0]
        self.answer(learned, *[True] * Progress.LEARNED_AFTER)

        picked = self.progress.pick(words, 3)

        self.assertNotIn(learned, picked)


if __name__ == "__main__":
    unittest.main()
