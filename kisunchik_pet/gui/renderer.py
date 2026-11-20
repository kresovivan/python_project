# -*- coding: utf-8 -*-
"""Отрисовка картинки с прозрачностью прямо на рабочем столе.

Что это в жизни: "прозрачная плёнка". Обычное окно - это непрозрачный
прямоугольник. А layered-окно Windows умеет показывать картинку с
попиксельной прозрачностью: где котик - там котик, где пусто - там
виден рабочий стол.

Три подводных камня, ради которых этот класс писался аккуратно:

1. ctypes без прототипов режет 64-битные дескрипторы окон до int,
   и UpdateLayeredWindow молча ничего не рисует. Поэтому внизу у
   каждой функции прописаны argtypes и restype.
2. Структуры POINT, SIZE и прочие должны быть объявлены ДО того,
   как их имена попадут в argtypes - иначе NameError при старте.
3. Цвета в картинке надо заранее домножить на прозрачность
   (premultiplied alpha) - такого формата ждёт Windows.
"""

import ctypes
from ctypes import wintypes

import numpy as np


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class SIZE(ctypes.Structure):
    _fields_ = [("cx", ctypes.c_long), ("cy", ctypes.c_long)]


class BLENDFUNCTION(ctypes.Structure):
    _fields_ = [
        ("BlendOp", ctypes.c_ubyte),
        ("BlendFlags", ctypes.c_ubyte),
        ("SourceConstantAlpha", ctypes.c_ubyte),
        ("AlphaFormat", ctypes.c_ubyte),
    ]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", ctypes.c_long),
        ("biHeight", ctypes.c_long),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", ctypes.c_long),
        ("biYPelsPerMeter", ctypes.c_long),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", wintypes.DWORD * 3)]


GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x80000
WS_EX_TOPMOST = 0x8
ULW_ALPHA = 2
AC_SRC_OVER = 0
AC_SRC_ALPHA = 1
DIB_RGB_COLORS = 0
SWP_NOSIZE = 0x1
SWP_NOZORDER = 0x4
SWP_NOACTIVATE = 0x10


def _declare_prototypes(user32, gdi32):
    """Прототипы функций: без них ctypes ломает 64-битные дескрипторы."""
    user32.GetDC.restype = wintypes.HDC
    user32.GetDC.argtypes = [wintypes.HWND]
    user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
    user32.GetWindowLongPtrW.restype = ctypes.c_longlong
    user32.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.SetWindowLongPtrW.restype = ctypes.c_longlong
    user32.SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_longlong]
    user32.UpdateLayeredWindow.restype = wintypes.BOOL
    user32.UpdateLayeredWindow.argtypes = [
        wintypes.HWND, wintypes.HDC, ctypes.POINTER(POINT), ctypes.POINTER(SIZE),
        wintypes.HDC, ctypes.POINTER(POINT), wintypes.DWORD,
        ctypes.POINTER(BLENDFUNCTION), wintypes.DWORD,
    ]
    user32.SetWindowPos.restype = wintypes.BOOL
    user32.SetWindowPos.argtypes = [
        wintypes.HWND, wintypes.HWND,
        ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT,
    ]
    gdi32.CreateCompatibleDC.restype = wintypes.HDC
    gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
    gdi32.CreateDIBSection.restype = wintypes.HBITMAP
    gdi32.CreateDIBSection.argtypes = [
        wintypes.HDC, ctypes.c_void_p, wintypes.UINT,
        ctypes.POINTER(ctypes.c_void_p), wintypes.HANDLE, wintypes.DWORD,
    ]
    gdi32.SelectObject.restype = wintypes.HGDIOBJ
    gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
    gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
    gdi32.DeleteDC.argtypes = [wintypes.HDC]


class LayeredRenderer:
    """Рисует картинки PIL в layered-окно поверх всех окон."""

    def __init__(self, log=None):
        self.user32 = ctypes.windll.user32
        self.gdi32 = ctypes.windll.gdi32
        _declare_prototypes(self.user32, self.gdi32)
        self._log = log  # функция записи в журнал, может быть None

    def make_layered(self, hwnd: int) -> None:
        """Включить окну режим попиксельной прозрачности."""
        style = self.user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
        self.user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED)

    def move(self, hwnd: int, x: int, y: int) -> None:
        """Переместить окно без изменения размера и без активации."""
        self.user32.SetWindowPos(hwnd, None, x, y, 0, 0,
                                 SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE)

    def push(self, hwnd: int, img_rgba, x: int, y: int) -> bool:
        """Нарисовать картинку RGBA: окно примет её размер и позицию.

        Возвращает True, если Windows приняла кадр.
        """
        width, height = img_rgba.size
        arr = np.asarray(img_rgba, dtype=np.uint8)
        alpha = arr[..., 3:4].astype(np.uint16)
        bgr = arr[..., [2, 1, 0]].astype(np.uint16)
        # Windows ждёт BGRA с заранее домноженной прозрачностью.
        premult = ((bgr * alpha + 127) // 255).astype(np.uint8)
        out = np.ascontiguousarray(np.concatenate([premult, arr[..., 3:4]], axis=2))
        data = out.tobytes()

        hdc_screen = self.user32.GetDC(None)
        hdc_mem = self.gdi32.CreateCompatibleDC(hdc_screen)
        bmi = BITMAPINFO()
        bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.bmiHeader.biWidth = width
        bmi.bmiHeader.biHeight = -height  # минус - строки идут сверху вниз
        bmi.bmiHeader.biPlanes = 1
        bmi.bmiHeader.biBitCount = 32
        bmi.bmiHeader.biCompression = 0
        bits = ctypes.c_void_p()
        hbmp = self.gdi32.CreateDIBSection(
            hdc_screen, ctypes.cast(ctypes.byref(bmi), ctypes.c_void_p),
            DIB_RGB_COLORS, ctypes.byref(bits), None, 0,
        )
        if not hbmp:
            self.user32.ReleaseDC(None, hdc_screen)
            self._report("CreateDIBSection вернул пустой битмап")
            return False
        ctypes.memmove(bits, data, len(data))
        old = self.gdi32.SelectObject(hdc_mem, hbmp)

        blend = BLENDFUNCTION(AC_SRC_OVER, 0, 255, AC_SRC_ALPHA)
        ok = self.user32.UpdateLayeredWindow(
            hwnd, hdc_screen, ctypes.byref(POINT(x, y)), ctypes.byref(SIZE(width, height)),
            hdc_mem, ctypes.byref(POINT(0, 0)), 0, ctypes.byref(blend), ULW_ALPHA,
        )
        if not ok:
            self._report(f"UpdateLayeredWindow не принял кадр, код {ctypes.get_last_error()}")

        self.gdi32.SelectObject(hdc_mem, old)
        self.gdi32.DeleteObject(hbmp)
        self.gdi32.DeleteDC(hdc_mem)
        self.user32.ReleaseDC(None, hdc_screen)
        return bool(ok)

    def _report(self, message: str) -> None:
        if self._log:
            try:
                self._log(message)
            except Exception:
                pass
