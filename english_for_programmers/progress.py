# =============================================================================
# ПРОГРЕСС — сколько раз на каждое слово ответили верно и неверно
# =============================================================================
#
# Хранится в progress.json:
#   {"variable": {"right": 3, "wrong": 1}, "loop": {"right": 0, "wrong": 2}}

import json
import random
from pathlib import Path

from models import Word


class Progress:
    """Статистика ответов + выбор слов для следующего занятия."""

    # Константы класса — общие для всех объектов Progress.
    LEARNED_AFTER = 3  # сколько верных ответов нужно, чтобы слово считалось выученным

    def __init__(self, path: Path):
        self._path = path
        self._data: dict[str, dict[str, int]] = self._load()

    # --- файл ----------------------------------------------------------------

    def _load(self) -> dict:
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            # Файла ещё нет или он испорчен — начинаем с нуля.
            return {}

    def _save(self) -> None:
        text = json.dumps(self._data, ensure_ascii=False, indent=2)
        self._path.write_text(text, encoding="utf-8")

    # --- запись ответов ------------------------------------------------------

    def record(self, word: Word, is_right: bool) -> None:
        """Запомнить ответ на слово и сразу сохранить в файл."""
        stats = self._data.setdefault(word.en, {"right": 0, "wrong": 0})
        stats["right" if is_right else "wrong"] += 1
        self._save()

    # --- состояние слова -----------------------------------------------------

    def _stats(self, word: Word) -> tuple[int, int]:
        stats = self._data.get(word.en, {"right": 0, "wrong": 0})
        return stats["right"], stats["wrong"]

    def is_new(self, word: Word) -> bool:
        """На слово ещё ни разу не отвечали."""
        return word.en not in self._data

    def is_learned(self, word: Word) -> bool:
        right, wrong = self._stats(word)
        return right >= self.LEARNED_AFTER and right > wrong

    def is_weak(self, word: Word) -> bool:
        """Слово, в котором ошибались не реже, чем отвечали верно."""
        right, wrong = self._stats(word)
        return wrong > 0 and wrong >= right

    # --- подбор слов для занятия ---------------------------------------------

    def pick(self, words: list[Word], size: int) -> list[Word]:
        """Выбрать size слов для занятия.

        Порядок важности:
          1. слабые слова (в них ошибались),
          2. новые слова,
          3. начатые, но ещё не выученные,
          4. уже выученные (для повторения).
        Внутри каждой группы — случайный порядок.
        """
        weak, new, started, learned = [], [], [], []
        for word in words:
            if self.is_weak(word):
                weak.append(word)
            elif self.is_new(word):
                new.append(word)
            elif self.is_learned(word):
                learned.append(word)
            else:
                started.append(word)

        result = []
        for group in (weak, new, started, learned):
            random.shuffle(group)
            result.extend(group)
        result = result[:size]
        random.shuffle(result)  # перемешиваем, чтобы слабые слова не шли подряд
        return result
