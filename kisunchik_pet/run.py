# -*- coding: utf-8 -*-
"""Точка входа: запускает Кисунчика на рабочем столе.

Запуск из папки проекта:
    python run.py

При запуске из собранного exe ресурсы (спрайты, словарь) лежат внутри
временной папки PyInstaller (sys._MEIPASS), а настройки и журнал - рядом
с exe-файлом, чтобы пользователь мог их менять и читать.
"""

import ctypes
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    # Запущены из exe: ресурсы во временной папке, настройки - рядом с exe.
    ASSETS_DIR = Path(sys._MEIPASS) / "assets"
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    ASSETS_DIR = Path(__file__).resolve().parent / "assets"
    BASE_DIR = Path(__file__).resolve().parent


def make_dpi_aware() -> None:
    """Сказать Windows, что мы сами считаем пиксели.

    Без этого на экране с масштабом 200% Windows врёт программе про
    размеры мониторов, и котик уезжает не туда.
    """
    try:
        # SetProcessDpiAwareness возвращает HRESULT, а не бросает
        # OSError при неудаче. Проверяем код возврата: S_OK = 0.
        hr = ctypes.windll.shcore.SetProcessDpiAwareness(2)
        if hr != 0:
            raise OSError(f"SetProcessDpiAwareness: {hr:#x}")
    except (AttributeError, OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass


def main() -> None:
    make_dpi_aware()
    # Импорт после make_dpi_aware: окно должно создаваться уже в режиме
    # честных пикселей.
    from core.settings import load
    from gui.app import KisunchikApp

    settings_path = BASE_DIR / "settings.json"
    app = KisunchikApp(
        assets_dir=ASSETS_DIR,
        log_path=BASE_DIR / "pet.log",
        settings=load(settings_path),
        settings_path=settings_path,
        progress_path=BASE_DIR / "progress.json",
    )
    app.run()


if __name__ == "__main__":
    main()
