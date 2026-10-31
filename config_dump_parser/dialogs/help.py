"""Окно инструкции пользователя."""

from typing import Dict, List, Optional

import tkinter as tk
from tkinter import ttk

from ..constants import COLORS, FONTS
from ..ui.widgets import CardFrame, CopyableLabel
from .help_content import ANCHORS, SECTIONS


class HelpWindow(tk.Toplevel):
    """Окно инструкции: разделы с текстом, шагами и примерами."""

    def __init__(self, parent: tk.Misc, anchor: str = 'start'):
        super().__init__(parent)
        self.title('Инструкция')
        self.geometry('1040x780')
        self.minsize(720, 480)
        self.transient(parent)
        self.configure(bg=COLORS['bg'])

        self._parent = parent
        self._canvas: Optional[tk.Canvas] = None
        self._content: Optional[tk.Frame] = None
        self._content_window_id: Optional[int] = None
        self._wheel_bound = False

        # Порядок сборки: header сверху, footer снизу, body растягивается.
        self._build_header()
        self._build_body()
        self._build_footer()

        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 1040) // 2
        y = parent.winfo_rooty() + 40
        self.geometry(f'1040x780+{max(0, x)}+{max(0, y)}')

        self.bind('<Escape>', lambda *_: self._close())
        self.protocol('WM_DELETE_WINDOW', self._close)

        self.after(50, lambda: self._scroll_to(anchor))

    # --- сборка окна ---

    def _build_header(self) -> None:
        """Шапка: заголовок + пояснение + разделитель."""
        header = tk.Frame(self, bg=COLORS['panel'])
        header.pack(fill=tk.X)

        hdr = tk.Frame(header, bg=COLORS['panel'])
        hdr.pack(fill=tk.X, padx=24, pady=18)

        tk.Label(hdr, text='Инструкция',
                 font=FONTS['title'],
                 fg=COLORS['text'], bg=COLORS['panel']
                 ).pack(anchor='w')

        tk.Label(
            hdr,
            text='Коротко о том, что делает программа и как ей '
                 'пользоваться. Если что-то непонятно - смотрите '
                 'соответствующий раздел.',
            font=FONTS['body'],
            fg=COLORS['text_muted'], bg=COLORS['panel'],
            justify=tk.LEFT,
        ).pack(anchor='w', pady=(6, 0))

        tk.Frame(self, height=1, bg=COLORS['border']).pack(fill=tk.X)

    def _build_body(self) -> None:
        """Тело: Canvas + вертикальный скролл + Frame контента."""
        container = tk.Frame(self, bg=COLORS['bg'])
        container.pack(fill=tk.BOTH, expand=True)

        self._canvas = tk.Canvas(container, highlightthickness=0,
                                 bg=COLORS['bg'])
        vsb = ttk.Scrollbar(container, orient='vertical',
                            command=self._canvas.yview,
                            style='Cyan.Vertical.TScrollbar')
        self._canvas.configure(yscrollcommand=vsb.set)

        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self._content = tk.Frame(self._canvas, bg=COLORS['bg'])
        self._content_window_id = self._canvas.create_window(
            (0, 0), window=self._content, anchor='nw')

        self._content.bind(
            '<Configure>',
            lambda e: self._canvas.configure(
                scrollregion=self._canvas.bbox('all')))

        self._canvas.bind(
            '<Configure>',
            lambda e: self._canvas.itemconfigure(
                self._content_window_id, width=e.width))

        self._render_sections()

        self._canvas.bind_all('<MouseWheel>', self._on_wheel)
        self._wheel_bound = True

    def _build_footer(self) -> None:
        """Подвал: разделитель + кнопка Закрыть."""
        footer = tk.Frame(self, bg=COLORS['panel'])
        footer.pack(fill=tk.X)

        tk.Frame(footer, height=1, bg=COLORS['border']).pack(fill=tk.X)

        ftr = tk.Frame(footer, bg=COLORS['panel'])
        ftr.pack(fill=tk.X, padx=24, pady=12)

        ttk.Button(ftr, text='Закрыть', style='Secondary.TButton',
                   command=self._close).pack(side=tk.RIGHT)

    # --- отрисовка разделов ---

    def _render_sections(self) -> None:
        for idx, (title, blocks) in enumerate(SECTIONS):
            self._render_section(idx, title, blocks)

    def _render_section(self, _idx: int, title: str,
                        blocks: List[Dict]) -> None:
        """Отрисовывает один раздел: заголовок + блоки."""
        outer = tk.Frame(self._content, bg=COLORS['bg'])
        outer.pack(fill=tk.X, padx=20, pady=(16, 6))

        tk.Label(outer, text=title, font=FONTS['section'],
                 fg=COLORS['accent'], bg=COLORS['bg']
                 ).pack(anchor='w')

        tk.Frame(outer, height=1, bg=COLORS['border']
                 ).pack(fill=tk.X, pady=(6, 10))

        for block in blocks:
            self._render_block(outer, block)

    def _render_block(self, parent: tk.Frame, block: Dict) -> None:
        """Рисует один блок: text / code / steps / samples / kv."""
        btype = block.get('type')

        if btype == 'text':
            tk.Label(
                parent, text=block.get('text', ''),
                font=FONTS['body'], fg=COLORS['text'], bg=COLORS['bg'],
                justify=tk.LEFT, anchor='w', wraplength=940,
            ).pack(anchor='w', fill=tk.X, pady=(0, 6))

        elif btype == 'code':
            box = CardFrame(parent)
            box.pack(fill=tk.X, pady=(4, 8))
            CopyableLabel(
                box, block.get('text', ''),
                app=self._parent,
                font=FONTS['mono'],
                fg=COLORS['pattern_fg'], bg=COLORS['panel'],
                justify=tk.LEFT, anchor='w',
            ).pack(anchor='w', padx=12, pady=10)

        elif btype == 'steps':
            for i, step in enumerate(block.get('items', []), 1):
                self._render_step_row(parent, i, step)

        elif btype == 'samples':
            for sample, note in block.get('items', []):
                self._render_sample_row(parent, sample, note)

        elif btype == 'kv':
            for key, val in block.get('items', []):
                self._render_kv_row(parent, key, val)

    def _render_step_row(self, parent: tk.Frame, number: int,
                         text: str) -> None:
        row = tk.Frame(parent, bg=COLORS['bg'])
        row.pack(fill=tk.X, pady=2)
        tk.Label(row, text=f'{number}.', font=FONTS['step_num'],
                 fg=COLORS['accent'], bg=COLORS['bg'],
                 width=3, anchor='nw').pack(side=tk.LEFT)
        CopyableLabel(
            row, text, app=self._parent,
            font=FONTS['body'], fg=COLORS['text'], bg=COLORS['bg'],
            justify=tk.LEFT, anchor='w', wraplength=920,
        ).pack(side=tk.LEFT, fill=tk.X)

    def _render_sample_row(self, parent: tk.Frame, sample: str,
                           note: str) -> None:
        """Строка «шаблон - пояснение» для раздела Поиск."""
        row = CardFrame(parent)
        row.pack(fill=tk.X, pady=2)

        inner = tk.Frame(row, bg=COLORS['panel'])
        inner.pack(fill=tk.X, padx=12, pady=6)
        inner.columnconfigure(0, minsize=180, weight=0)
        inner.columnconfigure(1, weight=1)

        CopyableLabel(
            inner, sample, app=self._parent, copy_value=sample,
            font=FONTS['mono'], fg=COLORS['pattern_fg'],
            bg=COLORS['panel'], anchor='w', justify=tk.LEFT,
        ).grid(row=0, column=0, sticky='nw', padx=(0, 16))

        CopyableLabel(
            inner, note, app=self._parent,
            font=FONTS['body'], fg=COLORS['text'], bg=COLORS['panel'],
            anchor='w', justify=tk.LEFT, wraplength=680,
        ).grid(row=0, column=1, sticky='ew')

    def _render_kv_row(self, parent: tk.Frame, key: str, val: str) -> None:
        """Строка «ключ - значение» в две колонки."""
        row = CardFrame(parent)
        row.pack(fill=tk.X, pady=2)

        inner = tk.Frame(row, bg=COLORS['panel'])
        inner.pack(fill=tk.X, padx=12, pady=8)
        inner.columnconfigure(0, minsize=240, weight=0)
        inner.columnconfigure(1, weight=1)

        CopyableLabel(
            inner, key, app=self._parent,
            font=FONTS['kv_key'], fg=COLORS['accent_dark'],
            bg=COLORS['panel'], anchor='nw', justify=tk.LEFT,
        ).grid(row=0, column=0, sticky='nw', padx=(0, 12))

        CopyableLabel(
            inner, val, app=self._parent,
            font=FONTS['body'], fg=COLORS['text'], bg=COLORS['panel'],
            anchor='w', justify=tk.LEFT, wraplength=680,
        ).grid(row=0, column=1, sticky='ew')

    # --- служебные ---

    def _scroll_to(self, anchor: str) -> None:
        """Прокрутка к разделу по якорю (start/open/columns/...)."""
        if not self._canvas:
            return
        idx = ANCHORS.get(anchor, 0)
        total = max(1, len(SECTIONS))
        self._canvas.yview_moveto(idx / total)

    def _on_wheel(self, event) -> None:
        try:
            self._canvas.yview_scroll(int(-1 * (event.delta / 120)),
                                      'units')
        except Exception:
            pass

    def _close(self) -> None:
        """Снимает bind_all и возвращает фокус родителю."""
        if self._wheel_bound:
            try:
                self.unbind_all('<MouseWheel>')
            except Exception:
                pass
            self._wheel_bound = False
        try:
            self._parent.focus_set()
        except Exception:
            pass
        self.destroy()