# =============================================================================
# ENGLISH FOR PROGRAMMERS - графическая версия. Точка входа.
# =============================================================================
#
# Запуск: откройте этот файл в VS Code и нажмите кнопку запуска справа вверху (Run Python File).
# Нужны библиотеки:  pip install customtkinter edge-tts
#
# Собрать exe с значком:  python build_exe.py   (готовый файл - в папке dist/)
#
# Устройство - см. README.md рядом с этим файлом.

import ctypes
import sys
from pathlib import Path

from gui.app import App


def resource_dir() -> Path:
    """Папка, где лежат data/ (слова) и assets/ (значок).

    Обычный запуск - папка с main.py. В exe (PyInstaller) программа при старте
    распаковывается во временную папку, её путь - в sys._MEIPASS.
    """
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))


def user_data_dir() -> Path:
    """Папка для прогресса и настроек.

    В exe - рядом с самим exe-файлом, а НЕ во временной папке: временная папка
    удаляется после закрытия программы, и прогресс бы пропадал.
    """
    if getattr(sys, "frozen", False):  # frozen - запущено как exe
        return Path(sys.executable).resolve().parent / "user_data"
    return Path(__file__).resolve().parent / "user_data"


def use_own_taskbar_icon() -> None:
    """Свой значок на панели задач Windows.

    Без этого при запуске через python.exe Windows считает окно "окном Python"
    и показывает на панели задач значок Python, а не значок программы.
    """
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("EnglishForProgrammers.App")
    except (AttributeError, OSError):
        pass  # не Windows или старая версия - ничего страшного


if __name__ == "__main__":
    use_own_taskbar_icon()
    App(resource_dir(), user_data_dir()).mainloop()
