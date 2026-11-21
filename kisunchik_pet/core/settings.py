# -*- coding: utf-8 -*-
"""Настройки питомца.

Что это в жизни: "панель с крутилками". Всё, что пользователь может
захотеть поменять, лежит здесь одним списком. Настройки хранятся
в файле settings.json рядом с программой и переживают перезапуск.
"""

import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path


@dataclass
class Settings:
    """Настройки котика со значениями по умолчанию."""

    scale: float = 0.75            # размер котика (0.5 - мелкий, 1.0 - крупный)
    sleep_after_idle: float = 180  # засыпает после стольких секунд тишины
    fun_every: float = 40          # затеи: примерно раз в столько секунд
    walk_every: float = 55         # прогулки: примерно раз в столько секунд
    auto_words: bool = True        # сам показывает слова в простое
    word_every: float = 420        # автопоказ слов: раз в столько секунд
    sound: bool = True             # озвучивать слова голосом
    walking: bool = True           # гулять по экрану самому
    autostart: bool = True         # запускаться вместе с Windows


def load(path: Path) -> Settings:
    """Прочитать настройки. Нет файла или он битый - вернуть умолчания."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return Settings()
    known = {f.name for f in fields(Settings)}
    clean = {k: v for k, v in data.items() if k in known}
    try:
        return Settings(**clean)
    except TypeError:
        return Settings()


def save(path: Path, settings: Settings) -> None:
    """Записать настройки на диск."""
    path.write_text(
        json.dumps(asdict(settings), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
