# =============================================================================
# СБОРКА EXE - программа в папке dist/EnglishForProgrammers/ + ярлык на рабочем столе
# =============================================================================
#
# Запуск:  python build_exe.py              - собрать и создать ярлык на рабочем столе
#          python build_exe.py --no-shortcut - только собрать
# Нужен PyInstaller:  pip install pyinstaller
#
# Что получается:
#   dist/EnglishForProgrammers/
#       EnglishForProgrammers.exe   - запуск программы (со значком)
#       _internal/                  - Python, библиотеки, слова и значок
#       user_data/                  - ваш прогресс и настройки
#   Ярлык "English for Programmers" на рабочем столе.
#
# Почему папка, а не один exe-файл: один файл при каждом запуске распаковывает
# себя во временную папку - окно появлялось через ~5 секунд. Папка запускается
# за ~1 секунду. Папку можно перенести куда угодно целиком (потом пересоздать ярлык).

import shutil
import subprocess
import sys
from pathlib import Path

import PyInstaller.__main__

ROOT = Path(__file__).resolve().parent
NAME = "EnglishForProgrammers"
TITLE = "English for Programmers"
APP_DIR = ROOT / "dist" / NAME
EXE = APP_DIR / f"{NAME}.exe"
SEP = ";" if sys.platform == "win32" else ":"  # разделитель в --add-data: "откуда;куда"


def build() -> None:
    PyInstaller.__main__.run(
        [
            str(ROOT / "main.py"),
            "--name", NAME,
            "--onedir",  # программа - папка с exe (быстрый запуск)
            "--windowed",  # без чёрного окна консоли
            "--icon", str(ROOT / "assets" / "icon.ico"),  # значок самого exe-файла
            "--add-data", f"{ROOT / 'data'}{SEP}data",  # слова
            "--add-data", f"{ROOT / 'assets'}{SEP}assets",  # значок для окна программы
            # CustomTkinter хранит темы оформления в файлах .json - их нужно взять с собой.
            "--collect-data", "customtkinter",
            "--distpath", str(ROOT / "dist"),
            "--workpath", str(ROOT / "build"),
            "--specpath", str(ROOT / "build"),
            "--noconfirm",
            "--clean",
        ]
    )


def copy_progress() -> None:
    """Перенести текущий прогресс к exe, чтобы не начинать заново (если там его ещё нет).

    Важно: после этого у exe и у запуска через python - РАЗНЫЕ копии прогресса.
    Пользуйтесь чем-то одним.
    """
    source, target = ROOT / "user_data", APP_DIR / "user_data"
    if source.exists() and not target.exists():
        shutil.copytree(source, target)
        print(f"Прогресс скопирован: {target}")


def create_shortcut() -> None:
    """Ярлык на рабочем столе. Создаём через PowerShell и стандартный объект Windows WScript.Shell."""
    script = (
        "$desktop = [Environment]::GetFolderPath('Desktop');"
        f"$link = (New-Object -ComObject WScript.Shell).CreateShortcut(\"$desktop\\{TITLE}.lnk\");"
        f"$link.TargetPath = '{EXE}';"
        f"$link.WorkingDirectory = '{APP_DIR}';"
        f"$link.IconLocation = '{EXE},0';"
        "$link.Description = 'Тренажёр английского для программистов';"
        "$link.Save();"
        "Write-Output \"$desktop\\" + TITLE + ".lnk\""
    )
    result = subprocess.run(["powershell", "-NoProfile", "-Command", script], capture_output=True, text=True)
    print("Ярлык:", result.stdout.strip() or result.stderr.strip())


if __name__ == "__main__":
    build()
    copy_progress()
    if "--no-shortcut" not in sys.argv:
        create_shortcut()
    print(f"\nГотово: {EXE}")
