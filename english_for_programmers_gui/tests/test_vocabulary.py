import random
import tempfile
import unittest
from pathlib import Path

from core.vocabulary import Vocabulary
from tests.support import DATA


class VocabularyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vocabulary = Vocabulary(DATA)

    def test_real_vocabulary_integrity(self):
        words = self.vocabulary.all_words()
        self.assertEqual(len(self.vocabulary), 3621)
        self.assertEqual(len(words), 3621)
        self.assertEqual(len(self.vocabulary.topics()), 18)
        self.assertEqual(len({word.en for word in words}), len(words))
        self.assertEqual(len({word.answer.casefold() for word in words}), len(words))
        self.assertTrue(all(word.en.strip() and word.ru.strip() and word.sound.strip() for word in words))
        self.assertTrue(all(self.vocabulary.get(word.en) is word for word in words))
        for topic in self.vocabulary.topics():
            self.assertTrue(self.vocabulary.words(topic))
            self.assertTrue(all(word.topic == topic for word in self.vocabulary.words(topic)))

    def test_every_word_has_three_distractors(self):
        for word in self.vocabulary.all_words():
            distractors = self.vocabulary.distractors(word)
            self.assertEqual(len(distractors), 3, word.en)
            self.assertNotIn(word.ru, distractors, word.en)

    def test_distractors_are_unique(self):
        random.seed(20260801)
        failures = []
        for word in self.vocabulary.all_words():
            for _ in range(40):
                distractors = self.vocabulary.distractors(word)
                if len(set(distractors)) != 3:
                    failures.append((word.en, distractors))
                    break
        self.assertFalse(failures, f"Повторяющиеся варианты у {len(failures)} слов: {failures[:3]}")

    def test_search_and_copy(self):
        self.assertTrue(any(word.en == "loop" for word in self.vocabulary.search("LOOP")))
        self.assertTrue(any("перемен" in word.ru for word in self.vocabulary.search("ПЕРЕМЕН")))
        topic = self.vocabulary.topics()[0]
        words = self.vocabulary.words(topic)
        words.clear()
        self.assertTrue(self.vocabulary.words(topic))

    def test_load_validation_and_deduplication(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            (path / "01.txt").write_text(
                "# topic: Тест\na|а|а\na (note)|другой|а\nb|б|б|пример\n",
                encoding="utf-8",
            )
            vocabulary = Vocabulary(path)
            self.assertEqual(len(vocabulary), 2)
            self.assertIsNone(vocabulary.get("a (note)"))
            self.assertEqual(vocabulary.get("b").example, "пример")
            (path / "bad.txt").write_text("broken\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "строка 1"):
                Vocabulary(path)


if __name__ == "__main__":
    unittest.main()
