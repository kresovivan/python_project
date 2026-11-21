# -*- coding: utf-8 -*-
"""Дневник обучения: на каком слове остановились и что уже видели.

Что это в жизни: "закладка в учебнике". По каждому блоку слов хранится
перемешанный порядок карточек и позиция закладки - сколько слов блока
уже пройдено. По каждому слову - сколько раз его показали и сколько
раз произнесли. Всё лежит в progress.json рядом с программой и
переживает выключение котика и компьютера.

Как по этому дневнику учат: новые слова берутся по закладке из самого
"отстающего" включённого блока (темы идут вровень), а примерно треть
показов - повторение уже виденных слов, причём редко виденные
выпадают чаще. Так работает простая карточная система: новое чередуется
с повторением.
"""

import json
import os
import random
import time
from datetime import date
from pathlib import Path


class ProgressStore:
    """Хранит порядок слов по блокам, позиции и счётчики показов."""

    def __init__(self, path: Path, rng: random.Random | None = None,
                 today=None):
        self._path = Path(path)
        self._rng = rng or random.Random()
        # today() -> "ГГГГ-ММ-ДД"; подменяется в тестах.
        self._today = today or (lambda: time.strftime("%Y-%m-%d"))
        self._data = {"categories": {}, "words": {}, "days": {},
                      "last_word": None}
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "categories" in data:
                self._data["categories"] = dict(data.get("categories") or {})
                self._data["words"] = dict(data.get("words") or {})
                self._data["days"] = dict(data.get("days") or {})
                self._data["last_word"] = data.get("last_word")
        except (OSError, json.JSONDecodeError):
            pass  # нет файла или он битый - начинаем с чистого листа
        self._dirty = False

    # --- порядок слов в блоке и закладка ---

    def deck(self, category_id: str, words: list[str]) -> list[str]:
        """Перемешанный порядок слов блока.

        Создаётся один раз и хранится: иначе после перезапуска котик
        начинал бы блок с другого места. Если состав блока поменялся
        (обновился словарь) - порядок собирается заново, закладка
        возвращается в начало.
        """
        entry = self._data["categories"].get(category_id)
        if entry is None or set(entry.get("order", [])) != set(words):
            order = list(words)
            self._rng.shuffle(order)
            entry = {"order": order, "pos": 0}
            self._data["categories"][category_id] = entry
            self._dirty = True
        return entry["order"]

    def position(self, category_id: str) -> int:
        """Закладка: сколько слов блока уже пройдено."""
        entry = self._data["categories"].get(category_id)
        return int(entry.get("pos", 0)) if entry else 0

    def advance(self, category_id: str) -> None:
        """Передвинуть закладку на одно слово вперёд."""
        entry = self._data["categories"].get(category_id)
        if entry is not None:
            entry["pos"] = min(int(entry.get("pos", 0)) + 1,
                               len(entry.get("order", [])))
            self._dirty = True

    def status(self, category_id: str, total: int) -> tuple[int, int]:
        """Для меню: (пройдено, всего) слов в блоке."""
        return min(self.position(category_id), total), total

    # --- счётчики по словам и дням ---

    def _bump_day(self, field: str) -> None:
        """Плюс один к сегодняшнему счётчику (для графика по дням)."""
        day = self._data["days"].setdefault(self._today(),
                                            {"shown": 0, "said": 0})
        day[field] = int(day.get(field, 0)) + 1

    def mark_shown(self, en: str) -> None:
        """Слово показали на карточке."""
        stats = self._data["words"].setdefault(en, {"shown": 0, "said": 0})
        stats["shown"] = int(stats.get("shown", 0)) + 1
        self._data["last_word"] = en
        self._bump_day("shown")
        self._dirty = True

    def mark_said(self, en: str) -> None:
        """Слово произнесли вслух."""
        stats = self._data["words"].setdefault(en, {"shown": 0, "said": 0})
        stats["said"] = int(stats.get("said", 0)) + 1
        self._bump_day("said")
        self._dirty = True

    def weekday_totals(self) -> tuple[list[int], list[int]]:
        """Слова по дням недели: (показано, произнесено), Пн..Вс."""
        shown = [0] * 7
        said = [0] * 7
        for day, counts in self._data["days"].items():
            try:
                wd = date.fromisoformat(day).weekday()
            except ValueError:
                continue
            shown[wd] += int(counts.get("shown", 0))
            said[wd] += int(counts.get("said", 0))
        return shown, said

    # --- управление прогрессом ---

    def reset_category(self, category_id: str) -> None:
        """Начать блок заново: закладка и порядок слов сбрасываются."""
        if category_id in self._data["categories"]:
            del self._data["categories"][category_id]
            self._dirty = True

    def reset_all(self) -> None:
        """Полный сброс: блоки, слова, дни, последнее слово."""
        self._data = {"categories": {}, "words": {}, "days": {},
                      "last_word": None}
        self._dirty = True

    def word_stats(self) -> dict:
        """Счётчики по всем словам: en -> {"shown": n, "said": n}."""
        return self._data["words"]

    def last_word(self) -> str | None:
        """Последнее показанное слово - с него продолжим после рестарта."""
        return self._data.get("last_word")

    # --- сохранение ---

    def save(self, force: bool = False) -> None:
        """Записать дневник на диск. Без изменений не пишет."""
        if not self._dirty and not force:
            return
        try:
            # Атомарная запись: сначала во временный файл, потом os.replace.
            # Иначе сбой посреди write_text оставит битый progress.json,
            # и весь дневник потеряется.
            tmp = self._path.with_name(self._path.name + ".tmp")
            tmp.write_text(
                json.dumps(self._data, ensure_ascii=False), encoding="utf-8")
            os.replace(tmp, self._path)
            self._dirty = False
        except OSError:
            pass  # диск занят или антивирус - попробуем в следующий раз
