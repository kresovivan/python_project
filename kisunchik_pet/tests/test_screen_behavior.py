# -*- coding: utf-8 -*-
"""Тесты поведения и границ экранов.

Здесь проверяется исправление главной жалобы: раньше котик не мог
уйти на второй монитор, потому что программа знала только главный экран.
Теперь границы считаются по виртуальному экрану - все мониторы вместе.
"""

import random
import unittest

from core.behavior import BehaviorPolicy
from gui.screen import ScreenArea, VirtualScreen


class TestScreenArea(unittest.TestCase):
    def test_clamp_inside_primary(self):
        area = ScreenArea(0, 0, 1920, 1080)
        self.assertEqual(area.clamp(100, 100, 128, 144), (100, 100))

    def test_clamp_edges(self):
        area = ScreenArea(0, 0, 1920, 1080)
        # Слишком далеко вправо-вниз - пододвинется к краю.
        self.assertEqual(area.clamp(5000, 5000, 128, 144), (1792, 936))
        # Отрицательные координаты - к левому верхнему углу.
        self.assertEqual(area.clamp(-500, -500, 128, 144), (0, 0))

    def test_clamp_allows_second_monitor_on_the_left(self):
        """Второй монитор слева имеет отрицательные координаты,
        и clamp обязан туда пускать."""
        area = ScreenArea(-1920, 0, 1920, 1080)  # два монитора бок о бок
        x, y = area.clamp(-1500, 400, 128, 144)
        self.assertEqual((x, y), (-1500, 400))


class TestVirtualScreenReal(unittest.TestCase):
    def test_virtual_covers_primary(self):
        """На реальном компьютере виртуальный экран не уже главного."""
        vs = VirtualScreen()
        self.assertGreaterEqual(vs.all.width, vs.primary.width)
        self.assertGreaterEqual(vs.all.height, vs.primary.height)
        self.assertGreater(vs.all.width, 0)


class TestBehaviorPolicy(unittest.TestCase):
    def test_walk_delta_stays_inside(self):
        """Прогулка никогда не выводит котика за пределы всех мониторов."""
        policy = BehaviorPolicy(rng=random.Random(7))
        left, right = -1920, 3840  # виртуальный экран из двух мониторов
        for pos in (left, -500, 0, 1000, right):
            delta = policy.walk_delta(pos, left, right)
            self.assertGreaterEqual(pos + delta, left)
            self.assertLessEqual(pos + delta, right)

    def test_walk_delta_can_go_left_of_zero(self):
        """Ходить можно и в отрицательные координаты (левый монитор)."""
        policy = BehaviorPolicy(rng=random.Random(3))
        left, right = -1920, 1920
        went_negative = any(
            0 + policy.walk_delta(0, left, right) < 0 for _ in range(50))
        self.assertTrue(went_negative, "котик ни разу не пошёл на левый монитор")


if __name__ == "__main__":
    unittest.main()
