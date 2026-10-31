"""Оформление виджетов Tkinter."""

import tkinter as tk
from tkinter import ttk

from ..config import COLORS, FONTS


class Theme:
    @staticmethod
    def apply(app) -> ttk.Style:
        style = ttk.Style(app)
        try:
            style.theme_use('clam')
        except Exception:
            pass

        style.configure('Accent.TButton', font=FONTS['button'],
                        foreground='white', background=COLORS['accent'],
                        borderwidth=0, focusthickness=0,
                        padding=(12, 6), relief='flat')
        style.map('Accent.TButton',
                  background=[('active', COLORS['accent_hover']),
                              ('pressed', COLORS['accent_dark']),
                              ('disabled', '#a9c4e5')],
                  foreground=[('disabled', '#eef3f8')])

        style.configure('Secondary.TButton', font=FONTS['button'],
                        foreground=COLORS['text'], background='#e8eaee',
                        borderwidth=0, focusthickness=0,
                        padding=(12, 6), relief='flat')
        style.map('Secondary.TButton',
                  background=[('active', '#d5d8dd'),
                              ('pressed', '#c2c6cc'),
                              ('disabled', '#f1f3f5')],
                  foreground=[('disabled', '#a6adb8')])

        style.configure('Small.TButton', font=FONTS['button'],
                        foreground=COLORS['text'], background='#e8eaee',
                        borderwidth=0, focusthickness=0,
                        padding=(8, 3), relief='flat')
        style.map('Small.TButton',
                  background=[('active', '#d5d8dd'), ('disabled', '#f1f3f5')],
                  foreground=[('disabled', '#a6adb8')])

        style.configure('Green.Horizontal.TProgressbar',
                        troughcolor=COLORS['border'], background='#4caf50',
                        darkcolor='#388e3c', lightcolor='#4caf50',
                        bordercolor=COLORS['border'], thickness=18)

        style.configure('Compare.Treeview',
                        font=FONTS['table_body'],
                        rowheight=30,
                        borderwidth=0)
        style.map('Compare.Treeview',
                  background=[('selected', COLORS['accent'])],
                  foreground=[('selected', 'white')])
        style.configure('Compare.Treeview.Heading',
                        font=FONTS['table_head'],
                        background='#eef1f5', foreground=COLORS['text'],
                        relief='flat', padding=(8, 8))
        style.map('Compare.Treeview.Heading',
                  background=[('active', '#dde3ea')])

        style.configure('Pick.Treeview',
                        font=FONTS['body'],
                        rowheight=24,
                        background=COLORS['panel'],
                        fieldbackground=COLORS['panel'],
                        foreground=COLORS['text'], borderwidth=0)
        style.map('Pick.Treeview',
                  background=[('selected', COLORS['accent'])],
                  foreground=[('selected', 'white')])
        style.configure('Pick.Treeview.Heading',
                        font=FONTS['h2'],
                        background='#eef1f5', foreground=COLORS['text'],
                        relief='flat', padding=(6, 4))
        style.map('Pick.Treeview.Heading',
                  background=[('active', '#dde3ea')])

        return style


class CardFrame(tk.Frame):
    def __init__(self, parent, **kwargs):
        kwargs.setdefault('bg', COLORS['panel'])
        kwargs.setdefault('highlightthickness', 1)
        kwargs.setdefault('highlightbackground', COLORS['border'])
        super().__init__(parent, **kwargs)
