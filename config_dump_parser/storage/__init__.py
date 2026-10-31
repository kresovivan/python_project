"""Хранилища: пути, настройки, префиксы."""

from .paths import AppPaths
from .settings import SettingsStore
from .markers import MarkersStore

__all__ = ['AppPaths', 'SettingsStore', 'MarkersStore']