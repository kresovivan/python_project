# -*- coding: utf-8 -*-
"""Виртуальный экран - все мониторы одним прямоугольником.

Что это в жизни: "карта стола". Если мониторов несколько, Windows
складывает их в один большой виртуальный прямоугольник. Левый монитор
может иметь отрицательные координаты - это нормально.

Именно из-за этого котик раньше не переходил на второй монитор:
программа знала только главный экран и не пускала его дальше края.
"""

import ctypes
from ctypes import wintypes
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

    def __init__(self, user32=None, monitors=None):
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
        # Список всех мониторов. В тестах подменяется своим списком,
        # чтобы не зависеть от реального железа.
        self.monitors = monitors if monitors is not None else self._enum_monitors()

    @staticmethod
    def _enum_monitors():
        """Прямоугольники всех мониторов в физических пикселях."""
        u = ctypes.windll.user32
        result = []
        MONITORENUMPROC = ctypes.WINFUNCTYPE(
            wintypes.BOOL, wintypes.HMONITOR, wintypes.HDC,
            ctypes.POINTER(wintypes.RECT), wintypes.LPARAM)

        def _cb(hmon, hdc, rect, lp):
            r = rect.contents
            result.append(ScreenArea(r.left, r.top, r.right, r.bottom))
            return True

        u.EnumDisplayMonitors(None, None, MONITORENUMPROC(_cb), 0)
        return result

    def area_at(self, x: int, y: int) -> ScreenArea:
        """Монитор, которому принадлежит точка.

        Если точка не попадает ни в один монитор (бывает у стыков
        экранов разной высоты), возвращаем ближайший по горизонтали.
        """
        for m in self.monitors:
            if m.left <= x < m.right and m.top <= y < m.bottom:
                return m
        # Ближайший монитор по расстоянию до центра точки.
        def dist(m):
            cx = min(max(x, m.left), m.right)
            cy = min(max(y, m.top), m.bottom)
            return (cx - x) ** 2 + (cy - y) ** 2
        return min(self.monitors, key=dist) if self.monitors else self.primary

    def clamp(self, x: int, y: int, w: int, h: int) -> tuple[int, int]:
        """Позиция внутри всех мониторов (перетаскивать можно везде)."""
        return self.all.clamp(x, y, w, h)
