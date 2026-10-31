"""Чтение и запись settings.json.

Важно: файл settings.json всегда лежит в дефолтной папке
(%APPDATA%\\ConfigDumpParser или рядом с exe в портативном режиме).
Поле settings_dir из файла игнорируется - иначе смена "папки настроек"
через UI приводила бы к потере файла при следующем запуске.
"""

import json
import os
from typing import Dict

from .paths import AppPaths


class SettingsStore:
    """Настройки приложения.

    Хранимые ключи:
      data_dir   - где хранится список префиксов (config_markers.json);
      xml_dir    - папка открытия XML по умолчанию;
      export_dir - папка сохранения CSV по умолчанию.

    Файл settings.json физически лежит всегда в AppPaths.default_settings_dir().
    Значение settings_dir в JSON сохраняется только для информации.
    """

    def __init__(self) -> None:
        self._settings = self._load()

    # --- публичный интерфейс ---

    def get(self, key: str, default: str = '') -> str:
        return self._settings.get(key, default)

    def set(self, key: str, value: str) -> None:
        self._settings[key] = value or ''

    def as_dict(self) -> Dict[str, str]:
        return dict(self._settings)

    def update(self, values: Dict[str, str]) -> None:
        self._settings.update(values)

    def settings_path(self) -> str:
        """Полный путь к файлу settings.json (только чтение)."""
        return AppPaths.settings_path()

    def save(self) -> None:
        """Пишет текущие значения в settings.json.

        Файл всегда пишется в дефолтную папку, а не туда, куда
        указывает settings_dir. Это гарантирует, что следующий
        запуск найдёт тот же файл.
        """
        path = AppPaths.settings_path()
        payload = {
            'settings_dir': AppPaths.default_settings_dir(),
            'data_dir': self._settings.get('data_dir', ''),
            'xml_dir': self._settings.get('xml_dir', ''),
            'export_dir': self._settings.get('export_dir', ''),
        }
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
        except OSError:
            pass
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    # --- внутренняя логика ---

    def _load(self) -> Dict[str, str]:
        """Читает settings.json из дефолтной папки.

        Никакой "миграции" между папками нет: если файла нет,
        используются значения по умолчанию. Поле settings_dir
        в результате всегда совпадает с дефолтной папкой.
        """
        default_dir = AppPaths.default_settings_dir()
        result = {
            'settings_dir': default_dir,
            'data_dir': default_dir,
            'xml_dir': '',
            'export_dir': '',
        }

        path = AppPaths.settings_path(default_dir)
        if not os.path.exists(path):
            return result

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return result
        except Exception:
            return result

        # settings_dir намеренно игнорируется из файла:
        # это всегда дефолтная папка, где физически лежит файл.
        dd = data.get('data_dir') or default_dir
        dd = os.path.abspath(os.path.expanduser(str(dd)))
        result['data_dir'] = dd

        result['xml_dir'] = str(data.get('xml_dir') or '')
        result['export_dir'] = str(data.get('export_dir') or '')
        return result