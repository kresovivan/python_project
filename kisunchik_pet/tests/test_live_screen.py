# -*- coding: utf-8 -*-
"""Тесты на реальном экране: окно, прозрачная отрисовка, голос Windows.

Эти тесты поднимают настоящее окно на рабочем столе, рисуют в него
красный квадрат и проверяют снимком экрана, что квадрат действительно
виден. Так мы ловим ошибки, которые юнит-тесты не видят: обрезанные
дескрипторы, рисование в служебное окно Tk, неверные координаты.
"""

import ctypes
import time
import unittest
from ctypes import wintypes
from pathlib import Path

import numpy as np
from PIL import Image, ImageGrab


def _make_dpi_aware():
    """Честные физические пиксели - как в run.py."""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass


_make_dpi_aware()

from gui.renderer import LayeredRenderer          # noqa: E402
from gui.screen import VirtualScreen              # noqa: E402
from gui.window import PetWindow, find_own_window, WINDOW_TITLE  # noqa: E402


def window_rect(hwnd):
    """Физические координаты окна."""
    r = wintypes.RECT()
    ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(r))
    return r.left, r.top, r.right, r.bottom


class TestLiveScreen(unittest.TestCase):
    """Настоящее окно + настоящий снимок экрана."""

    @classmethod
    def setUpClass(cls):
        cls.screen = VirtualScreen()
        cls.renderer = LayeredRenderer()
        cls.window = PetWindow(cls.screen, cls.renderer, (128, 144))
        cls.window.root.update()

    @classmethod
    def tearDownClass(cls):
        cls.window.root.destroy()

    def test_window_found_by_title(self):
        """Видимое окно находится по заголовку среди окон процесса."""
        hwnd = find_own_window(WINDOW_TITLE)
        self.assertIsNotNone(hwnd)
        self.assertEqual(hwnd, self.window.hwnd)

    def test_red_square_really_visible(self):
        """Рисуем красный квадрат - он обязан появиться на снимке экрана.

        Это сквозная проверка: если дескрипторы обрезаны или окно не то,
        квадрата на снимке не будет.
        """
        red = Image.new("RGBA", (128, 144), (255, 0, 0, 255))
        ok = self.renderer.push(self.window.hwnd, red,
                                self.window.pos_x, self.window.pos_y)
        self.assertTrue(ok, "UpdateLayeredWindow не принял кадр")
        time.sleep(0.3)  # дать Windows долю секунды на перерисовку

        left, top, right, bottom = window_rect(self.window.hwnd)
        self.assertEqual((right - left, bottom - top), (128, 144))

        shot = ImageGrab.grab(bbox=(left, top, right, bottom),
                              include_layered_windows=True)
        arr = np.asarray(shot.convert("RGB")).astype(int)
        red_share = ((arr[..., 0] > 180) & (arr[..., 1] < 90) & (arr[..., 2] < 90)).mean()
        self.assertGreater(red_share, 0.6,
                           f"красного на месте окна мало: {red_share:.0%}")

    def test_transparency_lets_desktop_through(self):
        """Прозрачные пиксели окна не закрашивают рабочий стол."""
        # Полностью прозрачный кадр.
        empty = Image.new("RGBA", (128, 144), (0, 0, 0, 0))
        self.assertTrue(self.renderer.push(self.window.hwnd, empty,
                                           self.window.pos_x, self.window.pos_y))
        time.sleep(0.3)
        left, top, right, bottom = window_rect(self.window.hwnd)
        # Снимок области окна не должен быть сплошным чёрным прямоугольником.
        shot = ImageGrab.grab(bbox=(left, top, right, bottom),
                              include_layered_windows=True)
        arr = np.asarray(shot.convert("RGB")).astype(int)
        black_share = ((arr[..., 0] < 10) & (arr[..., 1] < 10) & (arr[..., 2] < 10)).mean()
        self.assertLess(black_share, 0.5,
                        "прозрачный кадр выглядит чёрным квадратом")

    def test_move_to_second_monitor_area(self):
        """Окно свободно перемещается по всему виртуальному экрану."""
        area = self.screen.all
        target_x = area.left + 10  # самый левый край всех мониторов
        target_y = area.top + 10
        frame = Image.new("RGBA", (128, 144), (0, 128, 255, 255))
        self.renderer.push(self.window.hwnd, frame, target_x, target_y)
        time.sleep(0.2)
        left, top, _, _ = window_rect(self.window.hwnd)
        self.assertEqual((left, top), (target_x, target_y),
                         "окно не доехало до края виртуального экрана")
        # Возвращаем на место.
        self.renderer.push(self.window.hwnd, Image.new("RGBA", (128, 144), (0, 0, 0, 0)),
                           self.window.pos_x, self.window.pos_y)


class TestSpeaker(unittest.TestCase):
    def test_english_voice_available(self):
        """В Windows есть английский голос, и диктор готов говорить."""
        from core.speech import Speaker
        speaker = Speaker()
        try:
            deadline = time.time() + 5
            while not speaker.ready and speaker.error is None and time.time() < deadline:
                time.sleep(0.1)
            self.assertTrue(speaker.ready, speaker.error or "голос не поднялся")
            self.assertIsNotNone(speaker.voice)
        finally:
            speaker.close()


if __name__ == "__main__":
    unittest.main()
