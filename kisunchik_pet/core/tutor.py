# -*- coding: utf-8 -*-
"""Репетитор английского для питомца.

Что это в жизни: "коробка с карточками". Слова, которые пользователь знает
плохо, лежат сверху и попадаются чаще. Вес каждого слова посчитан из
прогресса в тренажёре english_for_programmers_gui.

Формат words.json: список [английское, перевод, транскрипция, вес].
Вес больше 1.0 - слово надо повторить, меньше 1.0 - уже хорошо знакомо.
"""

import json
import random
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Word:
    """Одна карточка: слово, перевод, как читается, вес повторения."""

    en: str
    ru: str
    transcription: str
    weight: float


class EnglishTutor:
    """Выбирает слова для показа с учётом весов."""

    def __init__(self, words_path: Path, rng: random.Random | None = None):
        with open(words_path, encoding="utf-8") as f:
            raw = json.load(f)
        self._words = [Word(en=w[0], ru=w[1], transcription=w[2], weight=float(w[3])) for w in raw]
        if not self._words:
            raise ValueError("словарь пуст")
        self._rng = rng or random.Random()
        # weights нужен random.choices - взвешенный случайный выбор
        self._weights = [w.weight for w in self._words]
        self._last: Word | None = None

    def __len__(self) -> int:
        return len(self._words)

    def next_word(self) -> Word:
        """Следующее слово. Подряд одно и то же не даём."""
        word = self._rng.choices(self._words, weights=self._weights, k=1)[0]
        if len(self._words) > 1:
            while word is self._last:
                word = self._rng.choices(self._words, weights=self._weights, k=1)[0]
        self._last = word
        return word
