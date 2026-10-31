"""Одна строка таблицы: разобранный элемент конфигурации."""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class MetadataRow:
    """Разобранный элемент конфигурации.

    Поля хранятся в словаре `data` - это позволяет динамически
    добавлять колонки, которых не было в базовом наборе.
    """

    data: Dict[str, str] = field(default_factory=dict)

    def get(self, key: str, default: str = '') -> str:
        return self.data.get(key, default)

    def set(self, key: str, value: str) -> None:
        self.data[key] = value