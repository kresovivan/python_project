# =============================================================================
# ОСНОВА ДЛЯ ТЕСТОВ ОКНА
# =============================================================================
#
# GuiTestCase открывает настоящее окно программы перед каждым тестом и
# закрывает после. Каждый тест получает новое окно и пустой временный
# user_data: тесты не зависят друг от друга и не трогают ваш прогресс.
#
# Голос заменён заглушкой FakeSpeaker. Настоящий голос запускает фоновый
# процесс PowerShell и ходит в интернет: это медленно и не нужно, чтобы
# проверить, ЧТО программа просит произнести.

import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

import customtkinter as ctk

from core.speech import DEFAULT_VOICE
from gui.app import App
from tests.support import CTRL, ROOT, SHIFT, event, pump


class FakeSpeaker:
    """Заглушка вместо core.speech.Speaker: ничего не говорит, только записывает.

    В spoken копятся пары (текст, медленно ли). Тест смотрит в этот список
    и проверяет, что программа попросила произнести нужное.
    """

    def __init__(self, cache_dir, voice=DEFAULT_VOICE):
        self.voice = voice
        self.spoken: list[tuple[str, bool]] = []

    def say(self, text, slow=False) -> bool:
        if not text:
            return False
        self.spoken.append((text, slow))
        return True

    def set_voice(self, voice) -> None:
        self.voice = voice

    # Остальное программа тоже вызывает, но тестам тут проверять нечего.
    def prefetch(self, text) -> None: ...

    def poll(self) -> None: ...

    def pop_message(self):
        return None

    def stop(self) -> None: ...

    def close(self) -> None: ...


class GuiTestCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="efp_gui_")
        self.addCleanup(tmp.cleanup)
        self.user_data = Path(tmp.name) / "user_data"
        # Тема оформления (тёмная/светлая) - общая настройка CustomTkinter
        # для всей программы. Запоминаем её и вернём после теста.
        self.addCleanup(ctk.set_appearance_mode, ctk.get_appearance_mode())
        self.app = self.open_app()

    def open_app(self) -> App:
        """Открыть окно программы. Его закроют после теста.

        data/ и assets/ берутся из проекта: программа их только читает.
        Всё, что программа пишет, попадает во временный user_data.
        """
        with patch("gui.app.Speaker", FakeSpeaker):
            app = App(ROOT, self.user_data)
        self.addCleanup(self.close_app, app)
        pump(app, 0.1)
        return app

    @staticmethod
    def close_app(app: App) -> None:
        """Закрыть окно, если тест не закрыл его сам."""
        try:
            exists = bool(app.winfo_exists())
        except tk.TclError:  # окно уже уничтожено: спрашивать его уже нельзя
            exists = False
        if exists:
            app.on_close()

    # --- удобные действия для тестов ----------------------------------------------

    @property
    def spoken(self) -> list[tuple[str, bool]]:
        """Что программа попросила произнести: [(текст, медленно), ...]."""
        return self.app.speaker.spoken

    def press(
        self,
        keysym: str,
        keycode: int = 0,
        ctrl: bool = False,
        shift: bool = False,
        app: App = None,
    ) -> None:
        """Нажать клавишу в окне: press("space"), press("т", 78, ctrl=True)."""
        app = app or self.app
        state = (CTRL if ctrl else 0) | (SHIFT if shift else 0)
        app._on_key(
            event(keysym, keycode, state)
        )  # так проверять клавиши велит CLAUDE.md
        pump(app, 0.02)

    def open_page(self, key: str):
        self.app.show_page(key)
        pump(self.app)
        return self.app.pages[key]

    @staticmethod
    def visible_screen(page):
        """Какой экран страницы занятия сейчас виден: page.intro, page.body или page.result.

        Видимый экран размещён через pack, у спрятанных менеджера размещения нет.
        """
        for screen in (page.intro, page.body, page.result):
            if screen.winfo_manager():
                return screen
        return None
