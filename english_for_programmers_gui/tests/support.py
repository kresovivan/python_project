# =============================================================================
# ОБЩИЕ ПОМОЩНИКИ ДЛЯ ТЕСТОВ
# =============================================================================
#
# Здесь лежит то, что нужно сразу многим тестам: пути к проекту, временный
# словарь, "нажатие клавиши", прокрутка цикла окна, функции Windows для
# проверки настоящего запуска программы.
#
# Правило: помощник не должен ничего проверять (assert). Проверки живут
# в самих тестах, чтобы по тесту было видно, ЧТО именно он требует.

import ctypes
import random
import shutil
import sys
import textwrap
import time
from pathlib import Path
from types import SimpleNamespace

from core.vocabulary import Vocabulary

ROOT = Path(__file__).resolve().parents[1]  # папка english_for_programmers_gui
DATA = ROOT / "data"  # настоящий словарь: 18 файлов .txt

# Биты поля event.state у tkinter: какие клавиши-модификаторы зажаты.
SHIFT = 0x0001
CTRL = 0x0004


# --- данные ------------------------------------------------------------------


def write_vocabulary(folder: Path, text: str) -> Vocabulary:
    """Создать маленький словарь из текста и загрузить его.

    Тестам логики не нужен настоящий словарь на 3621 слово: в маленьком
    сразу видно, какие слова есть, и тест не сломается, если в data/
    добавят новые слова. textwrap.dedent убирает общий отступ слева,
    чтобы текст можно было красиво написать внутри теста.
    """
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "01.txt").write_text(
        textwrap.dedent(text).strip() + "\n", encoding="utf-8"
    )
    return Vocabulary(folder)


def use_fixed_random(test, seed: int = 20260801) -> None:
    """Сделать случайные числа предсказуемыми на время одного теста.

    random.seed() меняет генератор для ВСЕЙ программы. Если не вернуть
    его состояние обратно, тест повлияет на тесты, которые идут после
    него. addCleanup() вызовет random.setstate() после теста, даже если
    тест упал.
    """
    state = random.getstate()
    random.seed(seed)
    test.addCleanup(random.setstate, state)


# --- окно программы --------------------------------------------------------------


def event(keysym: str, keycode: int = 0, state: int = 0) -> SimpleNamespace:
    """Поддельное событие нажатия клавиши - как будто его прислал tkinter.

    keysym - имя клавиши ("Return", "space", "F1", буква),
    keycode - номер физической клавиши (в русской раскладке буква другая,
    а номер тот же: P = 80, F = 70, N = 78, T = 84, H = 72),
    state - зажатые Ctrl/Shift (константы CTRL и SHIFT выше).
    """
    return SimpleNamespace(keysym=keysym, keycode=keycode, state=state)


def pump(app, seconds: float = 0.08) -> None:
    """Дать окну поработать: обработать отрисовку и отложенные задачи (after).

    В обычной программе это делает mainloop(), а в тесте его нет.
    """
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        app.update()
        time.sleep(0.01)
    app.update()


# --- настоящий запуск программы (только Windows) ---------------------------------


def copy_resources(target: Path) -> None:
    """Скопировать программу во временную папку, без user_data и кэшей."""
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "main.py", target / "main.py")
    shutil.copy2(ROOT / "build_exe.py", target / "build_exe.py")
    for name in ("core", "gui", "data", "assets"):
        shutil.copytree(
            ROOT / name,
            target / name,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            dirs_exist_ok=True,
        )


def titled_windows(title: str = "English for Programmers") -> list[int]:
    """Номера (hwnd) всех видимых окон Windows с таким заголовком."""
    if sys.platform != "win32":
        return []
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    found = []
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def collect(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            size = user32.GetWindowTextLengthW(hwnd) + 1
            buffer = ctypes.create_unicode_buffer(size)
            user32.GetWindowTextW(hwnd, buffer, size)
            if buffer.value == title:
                found.append(hwnd)
        return True

    user32.EnumWindows(callback_type(collect), 0)
    return found


def wait_for_new_window(previous: set[int], process, timeout: float = 30) -> int | None:
    """Дождаться окна программы, которого не было в previous.

    Возвращает hwnd окна или None, если окно не появилось или процесс
    завершился раньше. Решение "это ошибка" принимает сам тест.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        new = [hwnd for hwnd in titled_windows() if hwnd not in previous]
        if new:
            return new[0]
        if process.poll() is not None:
            return None
        time.sleep(0.1)
    return None


def send_wm_close(hwnd: int) -> None:
    """Послать окну WM_CLOSE - то же, что нажать крестик в углу окна."""
    wm_close = 0x0010
    response = ctypes.c_size_t()
    ctypes.windll.user32.SendMessageTimeoutW(
        hwnd, wm_close, 0, 0, 0, 5000, ctypes.byref(response)
    )
