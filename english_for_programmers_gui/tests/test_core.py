import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from core.answers import AnswerChecker
from core.errors_data import ERRORS
from core.lesson import ALL_TOPICS, WEAK_WORDS, Lesson
from core.models import Word
from core.progress import LEARNED, LEARNING, NEW, WEAK, Progress
from core.session import Session
from core.settings import Settings
from core.speech import VoiceEngine
from core.vocabulary import Vocabulary
from tests.support import DATA


class ModelsAndAnswersTests(unittest.TestCase):
    def test_word_answer_removes_notes(self):
        self.assertEqual(Word("commit (DB)", "фиксировать", "коммит", "Git").answer, "commit")
        self.assertEqual(Word("pretty (adv)", "довольно", "притти", "Слова").answer, "pretty")

    def test_answer_normalization(self):
        word = Word("It doesn't work!", "не работает", "", "Фразы")
        for answer in ("it doesn't work", "  IT DOESNT WORK!  ", "it   doesnt   work"):
            self.assertTrue(AnswerChecker.is_correct(answer, word))
        self.assertFalse(AnswerChecker.is_correct("it does work", word))

    def test_hint(self):
        self.assertEqual(AnswerChecker.hint("Can you"), "C _ _    _ _ _")
        self.assertEqual(AnswerChecker.hint("don't"), "d _ _ ' _")

    def test_session_properties_and_serialization(self):
        session = Session("cards", "Тема", ["a", "b"], index=1, right=1, mistakes=["b"])
        self.assertEqual((session.total, session.answered, session.percent, session.fraction), (2, 1, 100, 0.5))
        self.assertFalse(session.finished)
        self.assertEqual(Session.from_dict(session.to_dict()), session)
        self.assertEqual(Session("x", "y", []).percent, 0)


class ProgressSettingsLessonTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="efp_core_")
        self.root = Path(self.tmp.name)
        self.progress_path = self.root / "progress.json"
        self.settings_path = self.root / "state.json"
        self.progress = Progress(self.progress_path)
        self.settings = Settings(self.settings_path)
        self.vocabulary = Vocabulary(DATA)
        self.word = self.vocabulary.all_words()[0]

    def tearDown(self):
        self.tmp.cleanup()

    def test_progress_status_lifecycle_and_persistence(self):
        progress = self.progress
        self.assertEqual(progress.status(self.word), NEW)
        progress.record(self.word, False)
        self.assertEqual(progress.status(self.word), WEAK)
        progress.record(self.word, True)
        self.assertEqual(progress.status(self.word), WEAK)
        progress.record(self.word, True)
        self.assertEqual(progress.status(self.word), LEARNING)
        progress.record(self.word, True)
        self.assertEqual(progress.status(self.word), LEARNED)
        self.assertEqual(progress.today_total(), 4)
        self.assertEqual(len(progress.history()), 14)
        self.assertEqual(progress.streak(), 1)
        loaded = Progress(self.progress_path)
        self.assertEqual(loaded.status(self.word), LEARNED)
        self.assertEqual(loaded.today_total(), 4)
        loaded.reset()
        self.assertEqual(loaded.status(self.word), NEW)
        self.assertEqual(loaded.today_total(), 0)

    def test_streak_from_yesterday_and_broken_json(self):
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        before = (date.today() - timedelta(days=2)).isoformat()
        self.progress_path.write_text(
            json.dumps({"days": {yesterday: {"right": 1, "wrong": 0}, before: {"right": 1, "wrong": 0}}}),
            encoding="utf-8",
        )
        self.assertEqual(Progress(self.progress_path).streak(), 2)
        self.settings_path.write_text("{bad", encoding="utf-8")
        self.assertIsNone(Settings(self.settings_path).get("x"))

    def test_settings_save_restore_drop_and_fallback(self):
        first = Session("cards", "Тема", ["a", "b"], right=1)
        second = Session("typing", "Тема", ["c"])
        self.settings.save_session(first)
        self.settings.save_session(second)
        self.assertEqual(self.settings.last_session().mode, "typing")
        first.index = first.total
        self.settings.save_session(first)
        self.assertEqual(self.settings.last_session().mode, "typing")
        self.settings.drop_session("typing")
        self.assertIsNone(self.settings.last_session())
        self.assertIsNone(Settings(self.settings_path).last_session())

    def test_lesson_start_answer_restore_and_finish(self):
        lesson = Lesson("choice", self.vocabulary, self.progress, self.settings)
        self.assertTrue(lesson.start(ALL_TOPICS))
        self.assertEqual(lesson.session.total, Lesson.SIZE)
        word = lesson.current_word()
        lesson.answer(word, False)
        saved_index = lesson.session.index
        restored = Lesson("choice", self.vocabulary, Progress(self.progress_path), Settings(self.settings_path))
        self.assertTrue(restored.restore())
        self.assertEqual(restored.session.index, saved_index)
        self.assertEqual(restored.session.mistakes, [word.en])
        self.assertEqual(restored.current_word().en, lesson.session.keys[saved_index])
        while restored.active:
            restored.answer(restored.current_word(), True)
        self.assertIsNone(Settings(self.settings_path).session("choice"))
        self.assertIsNotNone(restored.session)
        self.assertEqual(restored.session.answered, Lesson.SIZE)

    def test_lesson_weak_words_and_retry(self):
        weak = self.vocabulary.all_words()[:3]
        for word in weak:
            self.progress.record(word, False)
        lesson = Lesson("cards", self.vocabulary, self.progress, self.settings)
        self.assertTrue(lesson.start(WEAK_WORDS))
        self.assertEqual(set(lesson.session.keys), {word.en for word in weak})
        lesson.answer(lesson.current_word(), False)
        lesson.answer(lesson.current_word(), True)
        self.assertTrue(lesson.retry_mistakes())
        self.assertEqual(lesson.session.total, 1)
        self.assertEqual(lesson.session.index, 0)
        self.assertEqual(lesson.session.mistakes, [])

    def test_lesson_skips_removed_words(self):
        good = self.vocabulary.all_words()[0].en
        self.settings.save_session(Session("typing", ALL_TOPICS, ["removed", good, "also removed"]))
        lesson = Lesson("typing", self.vocabulary, self.progress, self.settings)
        self.assertTrue(lesson.restore())
        self.assertEqual(lesson.current_word().en, good)
        self.assertEqual(lesson.session.index, 1)

    def test_topics_and_empty_weak_lesson(self):
        lesson = Lesson("cards", self.vocabulary, self.progress, self.settings)
        self.assertEqual(lesson.known_topic("удалённая тема"), ALL_TOPICS)
        self.assertEqual(lesson.neighbour_topic(ALL_TOPICS, 1), WEAK_WORDS)
        self.assertFalse(lesson.start(WEAK_WORDS))
        self.assertFalse(lesson.retry_mistakes())

    def test_errors_data_and_speech_preparation(self):
        self.assertEqual(len(ERRORS), 20)
        self.assertTrue(all(error.message and error.ru and error.words and error.hint for error in ERRORS))
        self.assertEqual(VoiceEngine.prepare("NameError: read_only ... next"), "Name Error: read only next")


if __name__ == "__main__":
    unittest.main()
