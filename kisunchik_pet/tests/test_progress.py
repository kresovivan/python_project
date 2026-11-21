# -*- coding: utf-8 -*-
"""Тесты дневника обучения и режима "учебник с закладкой".

Проверяем: порядок слов блока не меняется между запусками, закладка
переживает перезапуск, счётчики показов и произношений растут,
репетитор с дневником ведёт блоки вровень и повторяет виденное.
"""

import json
import random
import tempfile
import unittest
from pathlib import Path

from core.progress import ProgressStore
from core.tutor import EnglishTutor


def make_files(tmp: str):
    """Маленький словарь из двух блоков для тестов."""
    words = [["cat", "кот", "кэт", 1.0], ["dog", "пёс", "дог", 1.0],
             ["run", "бежать", "ран", 1.0], ["jump", "прыгать", "джамп", 1.0]]
    cats = {
        "categories": [
            {"id": "animals", "title": "Животные", "group": "topics"},
            {"id": "verbs", "title": "Глаголы", "group": "speech"},
        ],
        "words": {"cat": "animals", "dog": "animals",
                  "run": "verbs", "jump": "verbs"},
    }
    words_path = Path(tmp) / "words.json"
    cats_path = Path(tmp) / "categories.json"
    words_path.write_text(json.dumps(words), encoding="utf-8")
    cats_path.write_text(json.dumps(cats, ensure_ascii=False), encoding="utf-8")
    return words_path, cats_path


class TestProgressStore(unittest.TestCase):
    def test_deck_stable_across_restarts(self):
        """Порядок слов блока один и тот же после "перезапуска"."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "progress.json"
            store = ProgressStore(path, rng=random.Random(1))
            deck1 = store.deck("animals", ["cat", "dog"])
            store.save(force=True)
            store2 = ProgressStore(path)
            self.assertEqual(store2.deck("animals", ["cat", "dog"]), deck1)

    def test_position_survives_restart(self):
        """Закладка не слетает при выключении."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "progress.json"
            store = ProgressStore(path, rng=random.Random(1))
            store.deck("animals", ["cat", "dog"])
            store.advance("animals")
            store.save(force=True)
            store2 = ProgressStore(path)
            self.assertEqual(store2.position("animals"), 1)
            self.assertEqual(store2.status("animals", 2), (1, 2))

    def test_deck_rebuilt_when_words_change(self):
        """Состав блока поменялся - порядок собирается заново."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "progress.json"
            store = ProgressStore(path, rng=random.Random(1))
            store.deck("animals", ["cat", "dog"])
            store.advance("animals")
            deck = store.deck("animals", ["cat", "dog", "fox"])
            self.assertEqual(sorted(deck), ["cat", "dog", "fox"])
            self.assertEqual(store.position("animals"), 0)

    def test_counters_and_last_word(self):
        """Счётчики показов/произношений и последнее слово."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "progress.json"
            store = ProgressStore(path)
            store.mark_shown("cat")
            store.mark_said("cat")
            store.mark_shown("dog")
            store.save(force=True)
            store2 = ProgressStore(path)
            self.assertEqual(store2.word_stats()["cat"], {"shown": 1, "said": 1})
            self.assertEqual(store2.last_word(), "dog")

    def test_broken_file_is_fresh_start(self):
        """Битый дневник - просто начинаем с чистого листа."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "progress.json"
            path.write_text("{битый", encoding="utf-8")
            store = ProgressStore(path)
            self.assertEqual(store.position("animals"), 0)
            self.assertIsNone(store.last_word())

    def test_save_only_when_dirty(self):
        """Без изменений файл не трогаем."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "progress.json"
            store = ProgressStore(path)
            store.save()
            self.assertFalse(path.exists())
            store.mark_shown("cat")
            store.save()
            self.assertTrue(path.exists())


class TestTutorWithProgress(unittest.TestCase):
    def _make_tutor(self, tmp, seed=3):
        words_path, cats_path = make_files(tmp)
        store = ProgressStore(Path(tmp) / "progress.json",
                              rng=random.Random(seed))
        tutor = EnglishTutor(words_path, cats_path,
                             rng=random.Random(seed), progress=store)
        return tutor, store

    def test_new_words_follow_bookmark(self):
        """Новые слова идут по закладке, блоки продвигаются вровень."""
        with tempfile.TemporaryDirectory() as tmp:
            tutor, store = self._make_tutor(tmp)
            tutor.set_categories({"animals", "verbs"})
            seen = [tutor.next_word().en for _ in range(4)]
            # Каждый блок дал по слову, прежде чем начались повторы.
            self.assertEqual(store.position("animals") + store.position("verbs")
                             >= 2, True)
            self.assertTrue(set(seen) <= {"cat", "dog", "run", "jump"})

    def test_position_continues_after_restart(self):
        """После "перезапуска" репетитор продолжает с закладки."""
        with tempfile.TemporaryDirectory() as tmp:
            tutor, store = self._make_tutor(tmp)
            tutor.set_categories({"animals"})
            first_two = {tutor.next_word().en for _ in range(2)}
            store.save(force=True)
            self.assertEqual(first_two, {"cat", "dog"})
            self.assertEqual(store.position("animals"), 2)
            # "Новый" котик на том же файле: блок пройден, идёт повтор.
            tutor2, _store2 = self._make_tutor(tmp, seed=9)
            tutor2.set_categories({"animals"})
            word = tutor2.next_word()
            self.assertIn(word.en, {"cat", "dog"})

    def test_marks_shown(self):
        """Выданное слово само отмечается в дневнике."""
        with tempfile.TemporaryDirectory() as tmp:
            tutor, store = self._make_tutor(tmp)
            word = tutor.next_word()
            self.assertEqual(store.word_stats()[word.en]["shown"], 1)
            self.assertEqual(store.last_word(), word.en)

    def test_category_status_and_word_lookup(self):
        """Цифры для меню и поиск карточки по слову."""
        with tempfile.TemporaryDirectory() as tmp:
            tutor, store = self._make_tutor(tmp)
            self.assertEqual(tutor.category_status("animals"), (0, 2))
            tutor.set_categories({"animals"})
            tutor.next_word()
            self.assertEqual(tutor.category_status("animals"), (1, 2))
            self.assertEqual(tutor.word_by_en("cat").ru, "кот")
            self.assertIsNone(tutor.word_by_en("неттакого"))

    def test_without_progress_old_behaviour(self):
        """Без дневника репетитор работает как раньше."""
        with tempfile.TemporaryDirectory() as tmp:
            words_path, cats_path = make_files(tmp)
            tutor = EnglishTutor(words_path, cats_path, rng=random.Random(5))
            self.assertEqual(tutor.category_status("animals"), (0, 2))
            self.assertIsNotNone(tutor.next_word())


if __name__ == "__main__":
    unittest.main()
