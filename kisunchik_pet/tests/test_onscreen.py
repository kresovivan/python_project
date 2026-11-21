# -*- coding: utf-8 -*-
"""Котик всегда целиком на экране.

Регрессия: котик убегал за правый край монитора, если пузырь со словом
появлялся или прятался посреди прогулки (цель прогулки хранилась
в координатах окна, а окно при пузыре сдвигается). Плюс страховка
_keep_on_screen возвращает котика на монитор после любых сбоев.
"""

import unittest
from pathlib import Path

from gui.app import KisunchikApp
from gui.screen import ScreenArea, VirtualScreen

ASSETS = Path(__file__).resolve().parent.parent / "assets"
AREA = ScreenArea(0, 0, 1200, 800)


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


def make_app(clock):
    app = KisunchikApp(ASSETS, scale=0.5, clock=clock,
                       idle_probe=lambda: 0.0,
                       autostart_sync=lambda on: None)
    app.renderer.push = lambda *a, **k: True
    # Один монитор 1200x800 вместо реального железа.
    app.screen = VirtualScreen(monitors=[AREA])
    return app


def cat_rect(app):
    """Прямоугольник самого котика в экранных координатах."""
    w = app.window
    x = w.pos_x + (w.win_w - w.cat_w)
    y = w.pos_y + (w.win_h - w.cat_h)
    return x, y, x + w.cat_w, y + w.cat_h


class TestCatStaysOnScreen(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.app = make_app(self.clock)

    def tearDown(self):
        self.app.speaker.close()
        self.app.window.root.destroy()

    def _live(self, seconds):
        end = self.clock.now + seconds
        while self.clock.now < end:
            self.clock.advance(0.1)
            self.app.tick()

    def test_bubble_during_walk_keeps_cat_inside(self):
        """Пузырь посреди прогулки вправо не выталкивает котика за край."""
        app = self.app
        w = app.window
        # Котик у левого края, цель - правый край монитора.
        w.pos_x, w.pos_y = AREA.left, AREA.bottom - w.cat_h
        app.walk_target = AREA.right - w.cat_w
        app.state = "running_right"
        app.frame = 0
        # Пройти треть пути - и тут появляется пузырь (окно шире, левее).
        self._live(3)
        app.show_word()
        # Дожить прогулку с пузырём.
        self._live(60)
        x1, y1, x2, y2 = cat_rect(app)
        self.assertGreaterEqual(x1, AREA.left)
        self.assertLessEqual(x2, AREA.right, "котик за правым краем")
        self.assertGreaterEqual(y1, AREA.top)
        self.assertLessEqual(y2, AREA.bottom)

    def test_bubble_hides_during_walk_keeps_cat_inside(self):
        """Исчезновение пузыря посреди прогулки тоже безопасно."""
        app = self.app
        w = app.window
        w.pos_x, w.pos_y = AREA.left, AREA.bottom - w.cat_h
        app.show_word()  # пузырь уже есть
        app.walk_target = AREA.right - w.cat_w
        app.state = "running_right"
        app.frame = 0
        self._live(3)
        app.hide_word()
        self._live(60)
        _x1, _y1, x2, _y2 = cat_rect(app)
        self.assertLessEqual(x2, AREA.right, "котик за правым краем")

    def test_safety_net_returns_lost_cat(self):
        """Страховка возвращает котика, оказавшегося за краем."""
        app = self.app
        w = app.window
        # Сымитируем сбой: котик наполовину за правым краем.
        w.pos_x = AREA.right - w.cat_w // 2
        w.pos_y = AREA.bottom - w.cat_h
        # Ничего не планируем, один тик - страховка должна сработать.
        far = self.clock.now + 10000
        app.next_fun_at = app.next_walk_at = app.next_word_at = far
        self.clock.advance(0.1)
        app.tick()
        x1, y1, x2, y2 = cat_rect(app)
        self.assertGreaterEqual(x1, AREA.left)
        self.assertLessEqual(x2, AREA.right)
        self.assertGreaterEqual(y1, AREA.top)
        self.assertLessEqual(y2, AREA.bottom)


if __name__ == "__main__":
    unittest.main()
