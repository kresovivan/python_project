# =============================================================================
# ПРОГРЕСС - статистика по каждому слову и история занятий по дням
# =============================================================================
#
# Что это в жизни: "дневник ученика". В нём записано, сколько раз на каждое
# слово ответили верно и неверно, и сколько ответов было в каждый день.
# По дневнику решается, какое слово уже выучено, а какое слабое, и какие
# слова дать в следующем занятии.
#
# Файл user_data/progress.json (читает и пишет JsonStore из core/storage.py):
# {
#   "words": {"variable": {"right": 3, "wrong": 1, "last": "2026-11-01"}, ...},
#   "days":  {"2026-11-01": {"right": 25, "wrong": 7}, ...}
# }
#
# Кто пользуется: Lesson (core/lesson.py) записывает ответы и подбирает слова,
# страницы "Главная" и "Прогресс" показывают статистику.

import random
from collections.abc import Callable
from datetime import date, timedelta
from pathlib import Path

from core.models import Word
from core.storage import JsonStore

# Статусы слова. Константы вместо "магических строк": опечатка в имени
# константы сразу даст ошибку, а опечатка в строке "lerned" - нет.
NEW = "new"
WEAK = "weak"
LEARNING = "learning"
LEARNED = "learned"

STATUS_NAMES = {
    NEW: "Новое",
    WEAK: "Слабое",
    LEARNING: "Изучаю",
    LEARNED: "Выучено",
}


class Progress:
    """Статистика ответов, статусы слов, подбор слов для занятия."""

    LEARNED_AFTER = 3  # верных ответов, чтобы слово считалось выученным

    def __init__(self, path: Path, today: Callable[[], date] = date.today):
        """path - файл progress.json; today - "часы": функция, которая отвечает, какой сегодня день.

        Программа передаёт настоящие часы (date.today, по умолчанию). Тест
        передаёт свои, например lambda: date(2026, 11, 1), и сам решает,
        какой сегодня день. Без этого нельзя проверить, что будет в полночь.
        """
        self._today = today
        self._store = JsonStore(path)  # как хранить файл - забота JsonStore
        data = self._store.load()
        self._words: dict[str, dict] = data.get("words", {})
        self._days: dict[str, dict] = data.get("days", {})

    # --- файл ----------------------------------------------------------------

    @property
    def backup_path(self) -> Path | None:
        """Куда отложен испорченный файл прогресса (None - файл был в порядке)."""
        return self._store.backup_path

    def save(self) -> None:
        self._store.save({"words": self._words, "days": self._days})

    def reset(self) -> None:
        """Стереть весь прогресс."""
        self._words.clear()
        self._days.clear()
        self.save()

    # --- запись ответа -------------------------------------------------------

    def record(self, word: Word, is_right: bool) -> None:
        today = self._today().isoformat()  # "2026-11-01"
        key = "right" if is_right else "wrong"

        stats = self._words.setdefault(word.en, {"right": 0, "wrong": 0})
        stats[key] += 1
        stats["last"] = today

        day = self._days.setdefault(today, {"right": 0, "wrong": 0})
        day[key] += 1
        self.save()

    # --- статус слова --------------------------------------------------------

    def status(self, word: Word) -> str:
        stats = self._words.get(word.en)
        if stats is None:
            return NEW
        right, wrong = stats["right"], stats["wrong"]
        if wrong > 0 and wrong >= right:
            return WEAK
        if right >= self.LEARNED_AFTER and right > wrong:
            return LEARNED
        return LEARNING

    def counts(self, words: list[Word]) -> dict[str, int]:
        """Сколько слов в каждом статусе: {"new": 10, "weak": 2, ...}."""
        result = {NEW: 0, WEAK: 0, LEARNING: 0, LEARNED: 0}
        for word in words:
            result[self.status(word)] += 1
        return result

    # --- подбор слов ---------------------------------------------------------

    def pick(self, words: list[Word], size: int) -> list[Word]:
        """Порядок: слабые, новые, изучаемые, выученные. Внутри групп случайно."""
        groups = {NEW: [], WEAK: [], LEARNING: [], LEARNED: []}
        for word in words:
            groups[self.status(word)].append(word)

        result = []
        for status in (WEAK, NEW, LEARNING, LEARNED):
            random.shuffle(groups[status])
            result.extend(groups[status])
        result = result[:size]
        random.shuffle(result)
        return result

    # --- история по дням -----------------------------------------------------

    def history(self, days: int = 14) -> list[tuple[date, int, int]]:
        """Последние N дней: [(дата, верных, ошибок), ...] - от старых к новым."""
        today = self._today()
        result = []
        for offset in range(days - 1, -1, -1):
            day = today - timedelta(days=offset)
            stats = self._days.get(day.isoformat(), {"right": 0, "wrong": 0})
            result.append((day, stats["right"], stats["wrong"]))
        return result

    def today_total(self) -> int:
        stats = self._days.get(self._today().isoformat(), {"right": 0, "wrong": 0})
        return stats["right"] + stats["wrong"]

    def streak(self) -> int:
        """Сколько дней подряд (до сегодня или вчера) были занятия."""
        day = self._today()
        if day.isoformat() not in self._days:
            day -= timedelta(days=1)  # сегодня ещё не занимались - считаем со вчера
        count = 0
        while day.isoformat() in self._days:
            count += 1
            day -= timedelta(days=1)
        return count
