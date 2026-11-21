# -*- coding: utf-8 -*-
"""Тесты репетитора английского."""

import random
import unittest
from pathlib import Path

from core.tutor import EnglishTutor, Word

WORDS = Path(__file__).resolve().parent.parent / "assets" / "words.json"


class TestEnglishTutor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tutor = EnglishTutor(WORDS, rng=random.Random(42))

    def test_dictionary_loaded(self):
        """Словарь загрузился целиком: 4070 слов тренажёра + азбука."""
        self.assertEqual(len(self.tutor), 4110)

    def test_word_shape(self):
        """У слова есть все поля карточки."""
        word = self.tutor.next_word()
        self.assertIsInstance(word, Word)
        self.assertTrue(word.en)
        self.assertTrue(word.ru)
        self.assertTrue(word.transcription)
        self.assertGreater(word.weight, 0)

    def test_no_immediate_repeat(self):
        """Подряд одно и то же слово не выпадает."""
        words = [self.tutor.next_word() for _ in range(50)]
        for a, b in zip(words, words[1:]):
            self.assertIsNot(a, b)

    def test_weights_matter(self):
        """Слова с большим весом выпадают чаще.

        Берём искусственный словарь: одно тяжёлое слово и много лёгких.
        """
        import json, tempfile
        data = [["hard", "трудный", "хард", 10.0]]
        data += [[f"easy{i}", "лёгкое", "изи", 0.01] for i in range(100)]
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False,
                                         encoding="utf-8") as f:
            json.dump(data, f)
            tmp = f.name
        tutor = EnglishTutor(tmp, rng=random.Random(1))
        hits = sum(1 for _ in range(200) if tutor.next_word().en == "hard")
        self.assertGreater(hits, 50, "тяжёлое слово должно выпадать часто")


if __name__ == "__main__":
    unittest.main()
