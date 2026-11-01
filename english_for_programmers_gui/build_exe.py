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
#       user_data/                  - ваш прогресс и настройки exe-версии
#   Ярлык "English for Programmers" на рабочем столе.
#
# Почему папка, а не один exe-файл: один файл при каждом запуске распаковывает
# себя во временную папку - окно появлялось через ~5 секунд. Папка запускается
# за ~1 секунду. Папку можно перенести куда угодно целиком (потом пересоздать ярлык).
#
# Порядок сборки (см. низ файла):
#   1. keep_user_data   - унести user_data/ exe-версии в build/user_data_backup;
#   2. build            - PyInstaller стирает dist/EnglishForProgrammers и собирает заново;
#   3. keep_user_data   - вернуть user_data/ на место (даже если сборка упала);
#   4. copy_progress    - при самой первой сборке взять прогресс из запуска через python;
#   5. create_shortcut  - ярлык на рабочем столе.

import shutil
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NAME = "EnglishForProgrammers"
TITLE = "English for Programmers"
APP_DIR = ROOT / "dist" / NAME
EXE = APP_DIR / f"{NAME}.exe"
BACKUP_DIR = ROOT / "build" / "user_data_backup"  # где user_data/ пережидает сборку
SEP = ";" if sys.platform == "win32" else ":"  # разделитель в --add-data: "откуда;куда"


@contextmanager
def keep_user_data(app_dir: Path, backup_dir: Path) -> Iterator[None]:
    """Сберечь прогресс exe-версии, пока PyInstaller пересобирает её папку.

    Использование:
        with keep_user_data(APP_DIR, BACKUP_DIR):
            build()

    @contextmanager превращает функцию в "менеджер контекста" для with:
    код до yield выполняется при входе в with, код после yield - при выходе.
    try/finally гарантирует возврат данных, даже если сборка упала с ошибкой.
    """
    user_data = app_dir / "user_data"
    if backup_dir.exists():
        # Прошлая сборка оборвалась (например, закрыли окно терминала), и данные
        # остались в копии. Возможно, это единственные данные: не трогаем их.
        raise RuntimeError(
            f"Осталась копия прогресса от прерванной сборки: {backup_dir}\n"
            f"Перенесите её содержимое в {user_data} вручную и запустите сборку снова."
        )
    moved = user_data.exists()
    if moved:
        backup_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(user_data, backup_dir)
    try:
        yield
    finally:
        if moved:
            app_dir.mkdir(parents=True, exist_ok=True)  # сборка могла упасть до создания папки
            shutil.move(backup_dir, user_data)


def build() -> None:
    # Импорт здесь, а не в начале файла: тестам keep_user_data PyInstaller не нужен,
    # а загружается он заметно долго.
    import PyInstaller.__main__

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
    )  # fmt: skip


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
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", script], capture_output=True, text=True, check=False
    )
    print("Ярлык:", result.stdout.strip() or result.stderr.strip())


if __name__ == "__main__":
    with keep_user_data(APP_DIR, BACKUP_DIR):
        build()
    copy_progress()
    if "--no-shortcut" not in sys.argv:
        create_shortcut()
    print(f"\nГотово: {EXE}")
