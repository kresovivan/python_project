# =============================================================================
# ПРОГРЕСС - статистика по каждому слову и история занятий по дням
# =============================================================================
#
# Файл user_data/progress.json:
# {
#   "words": {"variable": {"right": 3, "wrong": 1, "last": "2026-11-01"}, ...},
#   "days":  {"2026-11-01": {"right": 25, "wrong": 7}, ...}
# }

import json
import random
from datetime import date, timedelta
from pathlib import Path

from core.models import Word

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

    def __init__(self, path: Path):
        self._path = path
        data = self._load()
        self._words: dict[str, dict] = data.get("words", {})
        self._days: dict[str, dict] = data.get("days", {})

    # --- файл ----------------------------------------------------------------

    def _load(self) -> dict:
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = {"words": self._words, "days": self._days}
        self._path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

    def reset(self) -> None:
        """Стереть весь прогресс."""
        self._words.clear()
        self._days.clear()
        self.save()

    # --- запись ответа -------------------------------------------------------

    def record(self, word: Word, is_right: bool) -> None:
        today = date.today().isoformat()  # "2026-11-01"
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
        today = date.today()
        result = []
        for offset in range(days - 1, -1, -1):
            day = today - timedelta(days=offset)
            stats = self._days.get(day.isoformat(), {"right": 0, "wrong": 0})
            result.append((day, stats["right"], stats["wrong"]))
        return result

    def today_total(self) -> int:
        stats = self._days.get(date.today().isoformat(), {"right": 0, "wrong": 0})
        return stats["right"] + stats["wrong"]

    def streak(self) -> int:
        """Сколько дней подряд (до сегодня или вчера) были занятия."""
        day = date.today()
        if day.isoformat() not in self._days:
            day -= timedelta(days=1)  # сегодня ещё не занимались - считаем со вчера
        count = 0
        while day.isoformat() in self._days:
            count += 1
            day -= timedelta(days=1)
        return count
