"""Чтение и запись config_markers.json (список префиксов)."""

import json
import os
from typing import List, Optional, Sequence

from ..constants import DEFAULT_MARKERS
from .paths import AppPaths


class MarkersStore:
    """Список префиксов кастомных объектов."""

    def __init__(self, data_dir: str) -> None:
        self.data_dir = data_dir
        self._markers: List[str] = self._load()

    # --- публичный интерфейс ---

    @property
    def items(self) -> List[str]:
        return list(self._markers)

    def set_items(self, markers: Sequence[str]) -> None:
        self._markers = [str(m) for m in markers if str(m).strip()]

    def is_custom_name(self, name: str) -> bool:
        """True, если имя начинается с одного из префиксов."""
        if not name:
            return False
        return any(name.startswith(m) for m in self._markers if m)

    def reload(self, new_data_dir: Optional[str] = None) -> None:
        """Перечитывает файл (при смене папки данных)."""
        if new_data_dir is not None:
            self.data_dir = new_data_dir
        self._markers = self._load()

    def save(self, target_dir: Optional[str] = None) -> None:
        """Записывает список префиксов в файл."""
        d = target_dir or self.data_dir
        os.makedirs(d, exist_ok=True)
        path = AppPaths.markers_path(d)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({'markers': list(self._markers)}, f,
                      ensure_ascii=False, indent=2)

    # --- внутренняя логика ---

    def _load(self) -> List[str]:
        path = AppPaths.markers_path(self.data_dir)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict) and isinstance(data.get('markers'), list):
                return [str(x) for x in data['markers'] if str(x).strip()]
            if isinstance(data, list):
                return [str(x) for x in data if str(x).strip()]
        except Exception:
            pass
        return list(DEFAULT_MARKERS)