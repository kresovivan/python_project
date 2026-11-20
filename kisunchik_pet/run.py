# -*- coding: utf-8 -*-
"""Точка входа: запускает Кисунчика на рабочем столе.

Запуск из папки проекта:
    python run.py
"""

import ctypes
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def make_dpi_aware() -> None:
    """Сказать Windows, что мы сами считаем пиксели.

    Без этого на экране с масштабом 200% Windows врёт программе про
    размеры мониторов, и котик уезжает не туда.
    """
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # per-monitor aware
    except (AttributeError, OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass


def main() -> None:
    make_dpi_aware()
    # Импорт после make_dpi_aware: окно должно создаваться уже в режиме
    # честных пикселей.
    from gui.app import KisunchikApp

    app = KisunchikApp(
        assets_dir=BASE_DIR / "assets",
        scale=0.5,
        log_path=BASE_DIR / "pet.log",
    )
    app.run()


if __name__ == "__main__":
    main()
