# Занятие (core/lesson.py, класс Lesson): выбор слов по теме, ответы,
# сохранение места остановки, повтор ошибок.
#
# Тесты работают с маленьким словарём из 5 слов, а не с настоящим:
# так видно, какие слова должны попасть в занятие.

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.lesson import ALL_TOPICS, WEAK_WORDS, Lesson
from core.progress import WEAK, Progress
from core.session import Session
from core.settings import Settings
from tests.support import use_fixed_random, write_vocabulary

VOCABULARY = """
    # topic: Циклы
    loop|цикл|луп
    break|прервать|брейк
    continue|продолжить|континью
    # topic: Git
    commit|фиксировать|коммит
    push|отправить|пуш
"""
LOOPS = {"loop", "break", "continue"}
GIT = {"commit", "push"}


class LessonTestCase(unittest.TestCase):
    def setUp(self):
        use_fixed_random(self)
        tmp = tempfile.TemporaryDirectory(prefix="efp_lesson_")
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.vocabulary = write_vocabulary(self.root / "data", VOCABULARY)
        self.progress = Progress(self.root / "progress.json")
        self.settings = Settings(self.root / "state.json")

    def new_lesson(self, mode: str = "cards") -> Lesson:
        return Lesson(mode, self.vocabulary, self.progress, self.settings)

    def lesson_after_restart(self, mode: str = "cards") -> Lesson:
        """Занятие, созданное заново из файлов - как при следующем запуске программы."""
        return Lesson(
            mode,
            self.vocabulary,
            Progress(self.root / "progress.json"),
            Settings(self.root / "state.json"),
        )

    def started(self, topic: str, mode: str = "cards") -> Lesson:
        lesson = self.new_lesson(mode)
        lesson.start(topic)
        return lesson


class StartTests(LessonTestCase):
    def test_lesson_takes_words_only_from_chosen_topic(self):
        lesson = self.new_lesson()

        lesson.start("Git")

        self.assertEqual(set(lesson.session.keys), GIT)

    def test_lesson_for_all_topics_takes_words_from_every_topic(self):
        lesson = self.new_lesson()

        lesson.start(ALL_TOPICS)

        self.assertEqual(set(lesson.session.keys), LOOPS | GIT)

    def test_lesson_is_not_longer_than_lesson_size(self):
        lesson = self.new_lesson()

        with patch.object(Lesson, "SIZE", 2):
            lesson.start(ALL_TOPICS)

        self.assertEqual(lesson.session.total, 2)

    def test_weak_words_lesson_takes_only_weak_words(self):
        self.progress.record(self.vocabulary.get("push"), False)
        lesson = self.new_lesson()

        lesson.start(WEAK_WORDS)

        self.assertEqual(lesson.session.keys, ["push"])

    def test_weak_words_lesson_does_not_start_without_weak_words(self):
        lesson = self.new_lesson()

        started = lesson.start(WEAK_WORDS)

        self.assertFalse(started)
        self.assertIsNone(lesson.session)

    def test_chosen_topic_is_remembered(self):
        self.started("Git")

        self.assertEqual(self.lesson_after_restart().last_topic, "Git")


class TopicListTests(LessonTestCase):
    def test_topic_list_starts_with_special_topics(self):
        self.assertEqual(
            self.new_lesson().topics, [ALL_TOPICS, WEAK_WORDS, "Циклы", "Git"]
        )

    def test_unknown_topic_is_replaced_with_all_topics(self):
        """Тему могли переименовать в data/, а в настройках осталось старое имя."""
        self.assertEqual(self.new_lesson().known_topic("Удалённая тема"), ALL_TOPICS)

    def test_next_topic_after_last_one_is_first(self):
        self.assertEqual(self.new_lesson().neighbour_topic("Git", 1), ALL_TOPICS)

    def test_previous_topic_before_first_one_is_last(self):
        self.assertEqual(self.new_lesson().neighbour_topic(ALL_TOPICS, -1), "Git")


class AnswerTests(LessonTestCase):
    def test_right_answer_is_counted_and_moves_to_next_word(self):
        lesson = self.started("Git")

        lesson.answer(lesson.current_word(), True)

        self.assertEqual((lesson.session.right, lesson.session.index), (1, 1))

    def test_wrong_answer_is_added_to_mistakes(self):
        lesson = self.started("Git")
        word = lesson.current_word()

        lesson.answer(word, False)

        self.assertEqual(lesson.session.wrong, 1)
        self.assertEqual(lesson.session.mistakes, [word.en])

    def test_answer_is_recorded_in_progress(self):
        lesson = self.started("Git")
        word = lesson.current_word()

        lesson.answer(word, False)

        self.assertEqual(self.progress.status(word), WEAK)

    def test_place_is_saved_right_after_answer(self):
        """Если закрыть программу сразу после ответа, ответ не засчитается дважды."""
        lesson = self.started("Git")

        lesson.answer(lesson.current_word(), True)

        self.assertEqual(Settings(self.root / "state.json").session("cards").index, 1)

    def test_lesson_ends_after_last_word(self):
        lesson = self.started("Git")

        while lesson.active:
            lesson.answer(lesson.current_word(), True)

        self.assertEqual(lesson.session.answered, len(GIT))
        self.assertIsNone(lesson.current_word())

    def test_finished_lesson_is_not_offered_to_continue(self):
        lesson = self.started("Git")

        while lesson.active:
            lesson.answer(lesson.current_word(), True)

        self.assertIsNone(Settings(self.root / "state.json").session("cards"))


class RestoreTests(LessonTestCase):
    def test_saved_lesson_continues_from_same_word(self):
        lesson = self.started("Циклы", mode="typing")
        lesson.answer(lesson.current_word(), True)
        expected = lesson.current_word()

        restored = self.lesson_after_restart("typing")

        self.assertTrue(restored.restore())
        self.assertEqual(restored.current_word(), expected)

    def test_nothing_to_restore_without_saved_lesson(self):
        self.assertFalse(self.new_lesson().restore())

    def test_restored_lesson_with_unknown_topic_uses_all_topics(self):
        self.settings.save_session(Session("cards", "Удалённая тема", ["loop"]))

        lesson = self.new_lesson()
        lesson.restore()

        self.assertEqual(lesson.session.topic, ALL_TOPICS)

    def test_words_removed_from_dictionary_are_skipped(self):
        self.settings.save_session(
            Session("typing", ALL_TOPICS, ["removed", "loop", "also removed"])
        )
        lesson = self.new_lesson("typing")
        lesson.restore()

        word = lesson.current_word()

        self.assertEqual(word.en, "loop")
        self.assertEqual(lesson.session.index, 1)


class RetryMistakesTests(LessonTestCase):
    def test_retry_takes_only_words_with_mistakes(self):
        lesson = self.started("Циклы")
        first = lesson.current_word()
        lesson.answer(first, False)
        lesson.answer(lesson.current_word(), True)
        third = lesson.current_word()
        lesson.answer(third, False)

        lesson.retry_mistakes()

        self.assertCountEqual(lesson.session.keys, [first.en, third.en])

    def test_retry_starts_new_lesson_from_first_word(self):
        lesson = self.started("Циклы")
        lesson.answer(lesson.current_word(), False)

        lesson.retry_mistakes()

        self.assertEqual((lesson.session.index, lesson.session.mistakes), (0, []))

    def test_word_with_several_mistakes_is_repeated_once(self):
        self.settings.save_session(Session("cards", "Циклы", ["loop", "loop"]))
        lesson = self.new_lesson()
        lesson.restore()
        lesson.answer(lesson.current_word(), False)
        lesson.answer(lesson.current_word(), False)

        lesson.retry_mistakes()

        self.assertEqual(lesson.session.keys, ["loop"])

    def test_no_retry_without_mistakes(self):
        lesson = self.started("Git")
        lesson.answer(lesson.current_word(), True)

        self.assertFalse(lesson.retry_mistakes())


if __name__ == "__main__":
    unittest.main()
