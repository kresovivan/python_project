# -*- coding: utf-8 -*-
"""Репетитор английского для питомца.

Что это в жизни: "коробка с карточками". Слова, которые пользователь знает
плохо, лежат сверху и попадаются чаще. Вес каждого слова посчитан из
прогресса в тренажёре english_for_programmers_gui.

Формат words.json: список [английское, перевод, транскрипция, вес].
Вес больше 1.0 - слово надо повторить, меньше 1.0 - уже хорошо знакомо.

Формат categories.json (необязателен): блоки слов по темам
("Программирование", "Глаголы"...) и карта слово -> блок. Репетитор
умеет выбирать слова только из разрешённых пользователем блоков.
"""

import json
import random
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Word:
    """Одна карточка: слово, перевод, как читается, вес повторения, блок."""

    en: str
    ru: str
    transcription: str
    weight: float
    category: str = ""


class EnglishTutor:
    """Выбирает слова для показа с учётом весов и разрешённых блоков."""

    def __init__(self, words_path: Path, categories_path: Path | None = None,
                 rng: random.Random | None = None):
        with open(words_path, encoding="utf-8") as f:
            raw = json.load(f)
        self._words = [Word(en=w[0], ru=w[1], transcription=w[2], weight=float(w[3]))
                       for w in raw]
        if not self._words:
            raise ValueError("словарь пуст")
        self._rng = rng or random.Random()
        self._last: Word | None = None

        # Блоки: id -> русское название, слово -> id блока.
        self._titles: dict[str, str] = {}
        self._groups: dict[str, list[dict]] = {}
        if categories_path is not None:
            try:
                data = json.loads(Path(categories_path).read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                data = None
            if data:
                self._titles = {c["id"]: c["title"] for c in data["categories"]}
                for c in data["categories"]:
                    self._groups.setdefault(c["group"], []).append(c)
                word_to_cat = data["words"]
                self._words = [
                    Word(en=w.en, ru=w.ru, transcription=w.transcription,
                         weight=w.weight, category=word_to_cat.get(w.en.lower(), ""))
                    for w in self._words
                ]
        self._enabled: set[str] | None = None  # None - все блоки разрешены

    def __len__(self) -> int:
        return len(self._words)

    # --- блоки ---

    def category_groups(self) -> dict[str, list[dict]]:
        """Блоки, сгруппированные для меню: группа -> список блоков."""
        return self._groups

    def category_title(self, category_id: str) -> str:
        """Русское название блока (для подписи на карточке)."""
        return self._titles.get(category_id, "")

    def set_categories(self, enabled: set[str] | None) -> None:
        """Разрешить только эти блоки. None или пусто - все."""
        self._enabled = set(enabled) if enabled else None

    def _pool(self) -> tuple[list[Word], list[float]]:
        """Слова, из которых можно выбирать, и их веса."""
        if self._enabled is None:
            return self._words, [w.weight for w in self._words]
        pool = [w for w in self._words if w.category in self._enabled]
        if not pool:
            # Пользователь отключил всё - честно учим всему,
            # хуже от этого не будет.
            return self._words, [w.weight for w in self._words]
        return pool, [w.weight for w in pool]

    def next_word(self) -> Word:
        """Следующее слово. Подряд одно и то же не даём."""
        pool, weights = self._pool()
        word = self._rng.choices(pool, weights=weights, k=1)[0]
        if len(pool) > 1:
            while word is self._last:
                word = self._rng.choices(pool, weights=weights, k=1)[0]
        self._last = word
        return word
