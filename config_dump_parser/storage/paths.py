"""Вычисление путей, которые использует программа."""

import os
import subprocess
import sys
from typing import Optional

from ..constants import APP_NAME, MARKERS_FILENAME, SETTINGS_FILENAME


class AppPaths:
    """Определяет, где хранить settings.json и config_markers.json.

    Логика:
      - обычный .py            -> рядом со скриптом;
      - .exe и рядом есть      -> рядом с .exe (портативный режим);
        settings.json
      - .exe без settings.json -> %APPDATA%\\<APP_NAME>
    """

    @staticmethod
    def program_dir() -> str:
        """Папка, где лежит .exe или .py."""
        if getattr(sys, 'frozen', False):
            return os.path.dirname(os.path.abspath(sys.executable))
        return os.path.dirname(os.path.abspath(__file__))

    @staticmethod
    def appdata_dir() -> str:
        """%APPDATA%\\<APP_NAME> с гарантированным созданием."""
        base = os.environ.get('APPDATA') or os.path.expanduser('~')
        folder = os.path.join(base, APP_NAME)
        try:
            os.makedirs(folder, exist_ok=True)
        except OSError:
            pass
        return folder

    @classmethod
    def default_settings_dir(cls) -> str:
        """Папка по умолчанию для settings.json и config_markers.json."""
        prog = cls.program_dir()
        if not getattr(sys, 'frozen', False):
            return prog
        if os.path.exists(os.path.join(prog, SETTINGS_FILENAME)):
            return prog
        return cls.appdata_dir()

    @classmethod
    def settings_path(cls, settings_dir: Optional[str] = None) -> str:
        """Полный путь к settings.json в указанной (или дефолтной) папке."""
        if settings_dir is None:
            settings_dir = cls.default_settings_dir()
        return os.path.join(settings_dir, SETTINGS_FILENAME)

    @staticmethod
    def markers_path(data_dir: str) -> str:
        """Полный путь к config_markers.json в папке данных."""
        return os.path.join(data_dir, MARKERS_FILENAME)

    @staticmethod
    def open_folder(path: str) -> None:
        """Открывает папку в системном проводнике/файловом менеджере."""
        try:
            if os.name == 'nt':
                os.startfile(path)  # type: ignore[attr-defined]
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', path])
            else:
                subprocess.Popen(['xdg-open', path])
        except Exception:
            pass