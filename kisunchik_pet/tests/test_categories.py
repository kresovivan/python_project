# -*- coding: utf-8 -*-
"""Тесты блоков слов и выбора голоса.

Проверяем без сети и без звука: репетитор фильтрует слова по блокам,
настройки с голосом и блоками переживают сохранение, SSML собирается
с темпом и высотой, в меню голосов есть онлайн-варианты.
"""

import json
import random
import tempfile
import unittest
from pathlib import Path

from core.settings import Settings, load, save
from core.speech import PERSONAS, ONLINE_VOICES, _ssml, voice_choices
from core.tutor import EnglishTutor

ASSETS = Path(__file__).resolve().parent.parent / "assets"


def make_files(tmp: str):
    """Маленький словарь из двух блоков для тестов."""
    words = [["cat", "кот", "кэт", 1.0], ["dog", "пёс", "дог", 1.0],
             ["run", "бежать", "ран", 1.0]]
    cats = {
        "categories": [
            {"id": "animals", "title": "Животные", "group": "topics"},
            {"id": "verbs", "title": "Глаголы", "group": "speech"},
        ],
        "words": {"cat": "animals", "dog": "animals", "run": "verbs"},
    }
    words_path = Path(tmp) / "words.json"
    cats_path = Path(tmp) / "categories.json"
    words_path.write_text(json.dumps(words), encoding="utf-8")
    cats_path.write_text(json.dumps(cats, ensure_ascii=False), encoding="utf-8")
    return words_path, cats_path


class TestCategoryFilter(unittest.TestCase):
    def test_filter_by_block(self):
        """С включённым одним блоком слова берутся только из него."""
        with tempfile.TemporaryDirectory() as tmp:
            words_path, cats_path = make_files(tmp)
            tutor = EnglishTutor(words_path, cats_path, rng=random.Random(7))
            tutor.set_categories({"verbs"})
            picked = {tutor.next_word().en for _ in range(10)}
            self.assertEqual(picked, {"run"})

    def test_none_means_everything(self):
        """Без фильтра доступны все слова."""
        with tempfile.TemporaryDirectory() as tmp:
            words_path, cats_path = make_files(tmp)
            tutor = EnglishTutor(words_path, cats_path, rng=random.Random(7))
            tutor.set_categories(None)
            picked = {tutor.next_word().en for _ in range(60)}
            self.assertEqual(picked, {"cat", "dog", "run"})

    def test_empty_filter_falls_back_to_all(self):
        """Фильтр, под который ничего не подходит, не ломает репетитора."""
        with tempfile.TemporaryDirectory() as tmp:
            words_path, cats_path = make_files(tmp)
            tutor = EnglishTutor(words_path, cats_path, rng=random.Random(7))
            tutor.set_categories({"нет_такого"})
            word = tutor.next_word()  # не должно упасть
            self.assertIn(word.en, {"cat", "dog", "run"})

    def test_category_title(self):
        """Русское название блока находится по id."""
        with tempfile.TemporaryDirectory() as tmp:
            words_path, cats_path = make_files(tmp)
            tutor = EnglishTutor(words_path, cats_path)
            self.assertEqual(tutor.category_title("animals"), "Животные")
            self.assertEqual(tutor.category_title("странное"), "")

    def test_groups_for_menu(self):
        """Блоки группируются для меню."""
        with tempfile.TemporaryDirectory() as tmp:
            words_path, cats_path = make_files(tmp)
            tutor = EnglishTutor(words_path, cats_path)
            groups = tutor.category_groups()
            self.assertIn("topics", groups)
            self.assertIn("speech", groups)

    def test_works_without_categories_file(self):
        """Без файла блоков репетитор работает как раньше."""
        with tempfile.TemporaryDirectory() as tmp:
            words_path, _ = make_files(tmp)
            tutor = EnglishTutor(words_path, rng=random.Random(1))
            self.assertEqual(len(tutor), 3)
            self.assertEqual(tutor.category_groups(), {})


class TestRealCategories(unittest.TestCase):
    def test_every_word_has_known_block(self):
        """В боевом словаре каждое слово отнесено к существующему блоку."""
        tutor = EnglishTutor(ASSETS / "words.json", ASSETS / "categories.json",
                             rng=random.Random(1))
        known = set()
        for cats in tutor.category_groups().values():
            known.update(c["id"] for c in cats)
        self.assertEqual(len(known), 18)
        word = tutor.next_word()
        self.assertIn(word.category, known)


class TestVoiceChoices(unittest.TestCase):
    def test_menu_has_personas_and_online(self):
        """В меню есть офлайн-персонажи и онлайн-голоса."""
        ids = [spec for spec, _label in voice_choices()]
        for persona, _label, _r, _p in PERSONAS:
            self.assertIn(persona, ids)
        for online, _label, _tld in ONLINE_VOICES:
            self.assertIn(online, ids)

    def test_ssml_rate_and_pitch(self):
        """SSML несёт темп, высоту и экранирование."""
        xml = _ssml("cat & dog", None, -2, 3)
        self.assertIn('absspeed="-2"', xml)
        self.assertIn('absmiddle="+3"', xml)
        self.assertIn("cat &amp; dog", xml)

    def test_ssml_voice_name(self):
        """Конкретный голос попадает в required=Name=..."""
        xml = _ssml("hello", "Microsoft Zira Desktop", 0, 0)
        self.assertIn('required="Name=Microsoft Zira Desktop"', xml)


class TestVoiceAndCategorySettings(unittest.TestCase):
    def test_roundtrip(self):
        """Голос и блоки переживают сохранение в файл."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            s = Settings(voice="gtts:co.uk", categories=["animals", "verbs"])
            save(path, s)
            loaded = load(path)
            self.assertEqual(loaded.voice, "gtts:co.uk")
            self.assertEqual(loaded.categories, ["animals", "verbs"])

    def test_defaults(self):
        """По умолчанию - автоголос и все блоки."""
        s = Settings()
        self.assertEqual(s.voice, "sapi:auto")
        self.assertIsNone(s.categories)


if __name__ == "__main__":
    unittest.main()
