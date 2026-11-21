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

Если передан дневник (ProgressStore), репетитор работает как учебник
с закладкой: новые слова идут по закладке из самого отстающего
включённого блока, примерно треть показов - повторение уже виденных
(редко виденные выпадают чаще). Без дневника - старый режим:
взвешенный случайный выбор по всему пулу.
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
                 rng: random.Random | None = None, progress=None):
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
        self._progress = progress              # дневник обучения или None
        self._by_en = {w.en: w for w in self._words}
        self._cat_cache: dict[str, list[Word]] = {}

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
        if self._progress is not None and self._groups:
            word = self._next_with_progress()
        else:
            pool, weights = self._pool()
            word = self._pick(pool, weights)
        self._last = word
        if self._progress is not None:
            self._progress.mark_shown(word.en)
        return word

    def _pick(self, pool: list[Word], weights: list[float]) -> Word:
        """Взвешенный случайный выбор без мгновенного повтора."""
        word = self._rng.choices(pool, weights=weights, k=1)[0]
        if len(pool) > 1:
            guard = 0
            while word is self._last and guard < 20:
                word = self._rng.choices(pool, weights=weights, k=1)[0]
                guard += 1
        return word

    # --- режим учебника с закладкой (нужен дневник) ---

    def _cat_words(self, category_id: str) -> list[Word]:
        """Слова блока (с кэшем)."""
        if category_id not in self._cat_cache:
            self._cat_cache[category_id] = [
                w for w in self._words if w.category == category_id]
        return self._cat_cache[category_id]

    def _enabled_category_ids(self) -> list[str]:
        """Включённые блоки в стабильном порядке меню."""
        ids = [c["id"] for cats in self._groups.values() for c in cats]
        if self._enabled is not None:
            ids = [i for i in ids if i in self._enabled]
        return ids

    def _next_with_progress(self) -> Word:
        """Новое слово по закладке или повторение виденного."""
        cat_ids = self._enabled_category_ids()
        stats = self._progress.word_stats()

        # Кандидаты на повторение: виденные слова включённых блоков.
        review_pool, review_weights = [], []
        # Блоки, где закладка ещё не дошла до конца.
        fresh = []
        for cid in cat_ids:
            words = self._cat_words(cid)
            deck = self._progress.deck(cid, [w.en for w in words])
            pos = self._progress.position(cid)
            if pos < len(deck):
                fresh.append((cid, pos / max(1, len(deck))))
            for w in words:
                shown = stats.get(w.en, {}).get("shown", 0)
                if shown:
                    review_pool.append(w)
                    review_weights.append(1.0 / shown)

        # Примерно треть показов - повторение; если новых не осталось -
        # только повторение.
        if review_pool and (not fresh or self._rng.random() < 0.35):
            return self._pick(review_pool, review_weights)
        if not fresh:
            # Включённые блоки пусты или всё выучено - страховка.
            pool, weights = self._pool()
            return self._pick(pool, weights)
        # Новое слово - из самого отстающего блока: темы идут вровень.
        best = min(ratio for _cid, ratio in fresh)
        cid = self._rng.choice([c for c, r in fresh if r == best])
        deck = self._progress.deck(cid, [w.en for w in self._cat_words(cid)])
        word = self._by_en[deck[self._progress.position(cid)]]
        self._progress.advance(cid)
        return word

    # --- сведения для меню и восстановления после перезапуска ---

    def category_status(self, category_id: str) -> tuple[int, int]:
        """(пройдено, всего) слов в блоке - для подписи в меню."""
        total = len(self._cat_words(category_id))
        if self._progress is None:
            return 0, total
        return self._progress.status(category_id, total)

    def word_by_en(self, en: str) -> Word | None:
        """Карточка по английскому слову (для показа последнего слова)."""
        return self._by_en.get(en)
