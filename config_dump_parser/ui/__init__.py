"""Пользовательский интерфейс: стили, виджеты, главное окно."""

from .formatting import fmt_number, human_size
from .widgets import CardFrame, CopyableLabel, ScrollableMixin

__all__ = [
    'fmt_number', 'human_size',
    'CardFrame', 'CopyableLabel', 'ScrollableMixin',
]