# -*- coding: utf-8 -*-
"""Виртуальный экран - все мониторы одним прямоугольником.

Что это в жизни: "карта стола". Если мониторов несколько, Windows
складывает их в один большой виртуальный прямоугольник. Левый монитор
может иметь отрицательные координаты - это нормально.

Именно из-за этого котик раньше не переходил на второй монитор:
программа знала только главный экран и не пускала его дальше края.
"""

import ctypes
from dataclasses import dataclass

# Константы GetSystemMetrics для виртуального экрана.
SM_XVIRTUALSCREEN = 76
SM_YVIRTUALSCREEN = 77
SM_CXVIRTUALSCREEN = 78
SM_CYVIRTUALSCREEN = 79
SM_CXSCREEN = 0
SM_CYSCREEN = 1


@dataclass(frozen=True)
class ScreenArea:
    """Прямоугольник в экранных координатах."""

    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top

    def clamp(self, x: int, y: int, w: int, h: int) -> tuple[int, int]:
        """Пододвинуть прямоугольник w x h так, чтобы он не вылезал наружу."""
        cx = min(max(x, self.left), max(self.left, self.right - w))
        cy = min(max(y, self.top), max(self.top, self.bottom - h))
        return cx, cy


class VirtualScreen:
    """Узнаёт у Windows границы всех мониторов и главного экрана."""

    def __init__(self, user32=None):
        u = user32 or ctypes.windll.user32
        x = u.GetSystemMetrics(SM_XVIRTUALSCREEN)
        y = u.GetSystemMetrics(SM_YVIRTUALSCREEN)
        w = u.GetSystemMetrics(SM_CXVIRTUALSCREEN)
        h = u.GetSystemMetrics(SM_CYVIRTUALSCREEN)
        self.all = ScreenArea(x, y, x + w, y + h)
        pw = u.GetSystemMetrics(SM_CXSCREEN)
        ph = u.GetSystemMetrics(SM_CYSCREEN)
        # Главный монитор всегда начинается в точке (0, 0).
        self.primary = ScreenArea(0, 0, pw, ph)

    def clamp(self, x: int, y: int, w: int, h: int) -> tuple[int, int]:
        """Позиция внутри всех мониторов (ходить можно везде)."""
        return self.all.clamp(x, y, w, h)
