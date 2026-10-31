"""Диалог выбора: экспортировать всё или только подсвеченное."""

from typing import Optional

import tkinter as tk
from tkinter import ttk

from ..constants import COLORS, FONTS
from ..ui.formatting import fmt_number
from ..ui.widgets import CardFrame


class ExportDialog(tk.Toplevel):
    """Спрашивает, что выгружать: все строки или подсвеченные."""

    def __init__(self, parent: tk.Misc, has_query: bool,
                 n_all: int, n_matched: int):
        super().__init__(parent)
        self.title('Экспорт в CSV')
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.configure(bg=COLORS['bg'])

        # result: 'all' / 'matched' / None (отмена).
        self.result: Optional[str] = None
        self.mode = tk.StringVar(value='matched' if has_query else 'all')

        card = CardFrame(self)
        card.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        inner = tk.Frame(card, bg=COLORS['panel'])
        inner.pack(fill=tk.BOTH, expand=True, padx=20, pady=18)

        tk.Label(inner, text='Что выгружать в CSV?',
                 font=FONTS['dialog'], fg=COLORS['text'],
                 bg=COLORS['panel']).pack(anchor='w', pady=(0, 12))

        self._radio(inner, f'Все строки ({fmt_number(n_all)})', 'all')
        self._radio(inner,
                    f'Только подсвеченные ({fmt_number(n_matched)})',
                    'matched', enabled=has_query)

        btns = tk.Frame(inner, bg=COLORS['panel'])
        btns.pack(fill=tk.X, pady=(18, 0))
        ttk.Button(btns, text='Отмена', style='Secondary.TButton',
                   command=self._cancel).pack(side=tk.RIGHT, padx=(6, 0))
        ttk.Button(btns, text='Экспорт', style='Accent.TButton',
                   command=self._ok).pack(side=tk.RIGHT)

        self._center_on_parent(parent, 380, 260)
        self.bind('<Return>', lambda *_: self._ok())
        self.bind('<Escape>', lambda *_: self._cancel())
        self.focus_set()

    def _radio(self, parent: tk.Frame, text: str, value: str,
               enabled: bool = True) -> None:
        rb = ttk.Radiobutton(parent, text=text,
                             variable=self.mode, value=value,
                             style='Card.TRadiobutton')
        rb.pack(anchor='w', pady=3, fill=tk.X)
        if not enabled:
            rb.state(['disabled'])

    def _center_on_parent(self, parent: tk.Misc, w: int, h: int) -> None:
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
        y = parent.winfo_rooty() + 150
        self.geometry(f'{w}x{h}+{x}+{y}')

    def _ok(self) -> None:
        self.result = self.mode.get()
        self.destroy()

    def _cancel(self) -> None:
        self.result = None
        self.destroy()