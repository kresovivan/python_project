# -*- coding: utf-8 -*-
"""Окно "О программе": кто сделал Кисунчика и как связаться.

Что это в жизни: "визитка". Открывается из пункта меню "Кисунчик" -
самый первый пункт, который раньше был просто серой надписью.
Почта кликабельна: открывает почтовую программу с готовым письмом.
"""

import tkinter as tk
import webbrowser
from tkinter import font as tkfont

from gui.progress_window import ACCENT, BG, FILL_DARK, SUBTLE, TEXT

APP_NAME = "Кисунчик"
APP_TAGLINE = "Настольный питомец - помощник в изучении английского"
AUTHOR = "Ivan Kresov"
AUTHOR_EMAIL = "iakresov@gmail.com"
VERSION = "1.4"


class AboutWindow:
    """Визитка программы. Один экземпляр на приложение."""

    def __init__(self, root: tk.Tk):
        self.win = tk.Toplevel(root)
        self.win.title("О программе")
        self.win.configure(bg=BG)
        self.win.attributes("-topmost", True)
        self.win.resizable(False, False)
        self.win.protocol("WM_DELETE_WINDOW", self.close)

        f_header = tkfont.Font(family="Segoe UI", size=15, weight="bold")
        f_text = tkfont.Font(family="Segoe UI", size=10)
        f_sub = tkfont.Font(family="Segoe UI", size=9)

        tk.Label(self.win, text=APP_NAME, bg=BG, fg=ACCENT,
                 font=f_header).pack(padx=24, pady=(18, 0))
        tk.Label(self.win, text=APP_TAGLINE, bg=BG, fg=TEXT,
                 font=f_text).pack(padx=24, pady=(2, 10))

        tk.Label(self.win, text=f"Версия {VERSION}", bg=BG, fg=SUBTLE,
                 font=f_sub).pack(padx=24)

        line = tk.Frame(self.win, bg=ACCENT, height=2)
        line.pack(fill="x", padx=24, pady=(10, 10))

        tk.Label(self.win, text=f"Автор: {AUTHOR}", bg=BG, fg=TEXT,
                 font=f_text).pack(padx=24, anchor="w")
        # Почта - ссылка: клик открывает письмо автору.
        mail = tk.Label(self.win, text=AUTHOR_EMAIL, bg=BG, fg=ACCENT,
                        font=f_text, cursor="hand2")
        mail.pack(padx=24, anchor="w", pady=(2, 0))
        mail.bind("<Button-1>", self._write_author)
        # Подчёркнутый шрифт создаём один раз: каждый <Enter> создавал
        # бы новый Tcl-шрифт (утечка при наведении).
        f_link = tkfont.Font(family="Segoe UI", size=10, underline=True)
        mail.bind("<Enter>", lambda _e: mail.configure(font=f_link))
        mail.bind("<Leave>", lambda _e: mail.configure(font=f_text))

        tk.Button(self.win, text="Закрыть", command=self.close,
                  font=f_text, bg=ACCENT, fg="#FFFFFF",
                  activebackground=FILL_DARK, activeforeground="#FFFFFF",
                  relief="flat", padx=14, pady=4,
                  cursor="hand2").pack(pady=18)

    def _write_author(self, _event) -> None:
        webbrowser.open(f"mailto:{AUTHOR_EMAIL}")

    def close(self) -> None:
        if self.win.winfo_exists():
            self.win.destroy()

    def is_alive(self) -> bool:
        return bool(self.win.winfo_exists())
