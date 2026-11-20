# -*- coding: utf-8 -*-
"""Окно питомца на tkinter.

Что это в жизни: "сцена". Сама по себе она невидимая - всё, что мы
видим, рисует LayeredRenderer. Сцена нужна, чтобы ловить мышку:
нажатия, перетаскивание, двойные клики, правую кнопку.

Два важных момента:

1. Tk создаёт ДВА окна - одно служебное и одно видимое. Рисовать надо
   в видимое, его ищем по заголовку среди окон нашего процесса.
2. Позицию окна двигаем через SetWindowPos, а не через Tk: Tk сам
   считает размер экрана и молча сдвигает окно, если координаты ему
   "не нравятся" (например, на втором мониторе).
"""

import ctypes
import tkinter as tk
from ctypes import wintypes

from gui.renderer import LayeredRenderer
from gui.screen import VirtualScreen

WINDOW_TITLE = "KisunchikPet"


def find_own_window(title: str):
    """Видимое верхнеуровневое окно нашего процесса с нужным заголовком."""
    user32 = ctypes.windll.user32
    found = []
    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    pid = ctypes.windll.kernel32.GetCurrentProcessId()

    def _cb(hwnd, lp):
        proc = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(proc))
        if proc.value == pid and user32.IsWindowVisible(hwnd):
            n = user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(n + 1)
            user32.GetWindowTextW(hwnd, buf, n + 1)
            if buf.value == title:
                found.append(hwnd)
        return True

    user32.EnumWindows(WNDENUMPROC(_cb), 0)
    return found[0] if found else None


class PetWindow:
    """Прозрачное окно поверх рабочего стола с обработкой мыши.

    События наружу отдаёт коллбеками:
      on_zone(zone)  - клик по котику: "head", "tail" или "belly"
      on_double()    - двойной клик
      on_exit()      - пользователь выбрал "Выход" в меню
    """

    def __init__(self, screen: VirtualScreen, renderer: LayeredRenderer,
                 cat_size: tuple[int, int]):
        self.screen = screen
        self.renderer = renderer
        self.cat_w, self.cat_h = cat_size

        self.root = tk.Tk()
        self.root.title(WINDOW_TITLE)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)

        # Стартовая позиция: правый нижний угол главного монитора.
        self.pos_x = self.screen.primary.right - self.cat_w - 40
        self.pos_y = self.screen.primary.bottom - self.cat_h - 60
        # Текущий размер окна равен размеру котика; когда показывается
        # пузырь, окно временно становится шире и выше.
        self.win_w = self.cat_w
        self.win_h = self.cat_h

        self.root.update()
        self.hwnd = find_own_window(WINDOW_TITLE) or self.root.winfo_id()
        self.renderer.make_layered(self.hwnd)
        self.renderer.move(self.hwnd, self.pos_x, self.pos_y)

        self.on_zone = None
        self.on_double = None
        self.on_exit = None

        self._drag_start = None
        self._dragging = False

        self.root.bind("<ButtonPress-1>", self._press)
        self.root.bind("<B1-Motion>", self._drag)
        self.root.bind("<ButtonRelease-1>", self._release)
        self.root.bind("<Double-Button-1>", self._double)
        self.root.bind("<Button-3>", self._menu)

        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu = self.menu
        self.menu.add_command(label="Кисунчик", state="disabled")
        self.menu.add_command(label="Выход", command=self._exit)

    # --- координаты ---

    def resize_for_bubble(self, extra_left: int, extra_top: int) -> None:
        """Расширить окно влево и вверх, чтобы рядом с котиком
        поместился пузырь. Котик при этом остаётся на том же месте
        экрана - сдвигается левый верхний угол окна."""
        self.win_w = self.cat_w + extra_left
        self.win_h = self.cat_h + extra_top
        self.pos_x -= extra_left
        self.pos_y -= extra_top

    def resize_cat_only(self) -> None:
        """Вернуть окно к размеру одного котика."""
        extra_left = self.win_w - self.cat_w
        extra_top = self.win_h - self.cat_h
        self.pos_x += extra_left
        self.pos_y += extra_top
        self.win_w = self.cat_w
        self.win_h = self.cat_h

    def cat_offset(self) -> tuple[int, int]:
        """Где внутри окна сейчас сидит котик (левый нижний угол)."""
        return self.win_w - self.cat_w, self.win_h - self.cat_h

    # --- мышь ---

    def _zone_at(self, x: int, y: int):
        """По какой части котика кликнули: head, tail, belly или None
        (клик мимо котика, например по области пузыря)."""
        off_x, off_y = self.cat_offset()
        rx = (x - off_x) / self.cat_w
        ry = (y - off_y) / self.cat_h
        if not (0 <= rx <= 1 and 0 <= ry <= 1):
            return None
        if ry < 0.45:
            return "head"
        if rx > 0.62:
            return "tail"
        return "belly"

    def _press(self, event):
        self._drag_start = (event.x_root, event.y_root, self.pos_x, self.pos_y)
        self._dragging = False

    def _drag(self, event):
        if not self._drag_start:
            return
        sx, sy, px, py = self._drag_start
        dx, dy = event.x_root - sx, event.y_root - sy
        if not self._dragging and abs(dx) + abs(dy) >= 6:
            self._dragging = True
        if self._dragging:
            # clamp по всем мониторам - котика можно перенести куда угодно
            self.pos_x, self.pos_y = self.screen.clamp(
                px + dx, py + dy, self.win_w, self.win_h)
            self.renderer.move(self.hwnd, self.pos_x, self.pos_y)

    def _release(self, event):
        if not self._dragging and self.on_zone:
            zone = self._zone_at(event.x, event.y)
            if zone:
                self.on_zone(zone)
        self._drag_start = None
        self._dragging = False

    def _double(self, event):
        if self.on_double:
            self.on_double()

    def _menu(self, event):
        self.menu.post(event.x_root, event.y_root)

    def _exit(self):
        if self.on_exit:
            self.on_exit()
