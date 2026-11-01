import ctypes
import shutil
import time
from ctypes import wintypes
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def event(name, code=0, state=0):
    return SimpleNamespace(keysym=name, keycode=code, state=state)


def pump(app, seconds=0.08):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        app.update()
        time.sleep(0.01)
    app.update()


def copy_resources(target: Path):
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


def titled_windows(title="English for Programmers"):
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


def wait_for_new_window(previous, process, timeout=25):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        new = [hwnd for hwnd in titled_windows() if hwnd not in previous]
        if new:
            return new[0]
        if process.poll() is not None:
            raise AssertionError(f"Процесс завершился до открытия окна: {process.returncode}")
        time.sleep(0.1)
    raise AssertionError("Окно приложения не появилось вовремя")


def send_wm_close(hwnd):
    response = ctypes.c_size_t()
    ctypes.windll.user32.SendMessageTimeoutW(hwnd, 0x0010, 0, 0, 0, 5000, ctypes.byref(response))


def close_process_stdout(process):
    if process and process.stdout and not process.stdout.closed:
        process.stdout.close()


def close_app(app):
    process = app.speaker.system._process
    try:
        app.on_close()
    finally:
        close_process_stdout(process)
