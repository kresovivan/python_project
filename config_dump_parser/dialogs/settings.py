"""Окно настроек: редактор путей к данным, XML и экспорту.

Поле "Папка настроек" из окна убрано. Файл settings.json всегда
лежит в дефолтной папке (%APPDATA%\\ConfigDumpParser или рядом
с exe в портативном режиме) - это гарантирует, что следующий
запуск найдёт тот же файл. Меняются только рабочие пути.
"""

import os
from typing import Dict, Optional

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from ..constants import APP_NAME, COLORS, FONTS
from ..storage import AppPaths
from ..ui.widgets import CardFrame, ScrollableMixin


class SettingsDialog(tk.Toplevel, ScrollableMixin):
    """Редактор путей: data_dir, xml_dir, export_dir."""

    BTN_WIDTH = 12

    def __init__(self, parent: tk.Misc, settings: Dict[str, str]):
        super().__init__(parent)
        self.title('Настройки')
        self.minsize(680, 460)
        self.transient(parent)
        self.grab_set()
        self.configure(bg=COLORS['bg'])

        # result: словарь новых значений / None (отмена).
        self.result: Optional[Dict[str, str]] = None
        self._settings = dict(settings)
        self.vars: Dict[str, tk.StringVar] = {}
        self._wheel_widgets = []

        self._canvas: Optional[tk.Canvas] = None
        self._scroll_canvas: Optional[tk.Canvas] = None
        self._content: Optional[tk.Frame] = None
        self._content_win_id: Optional[int] = None

        self._place_window(parent, 800, 620)
        self._build_ui()

        self.bind('<Configure>', lambda e: self._refresh_scrollregion())
        self.bind('<Escape>', lambda *_: self._cancel())
        self.protocol('WM_DELETE_WINDOW', self._cancel)

        self.after(50, self._refresh_scrollregion)

    # --- размещение ---

    def _place_window(self, parent: tk.Misc, w: int, h: int) -> None:
        self.update_idletasks()
        try:
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
        except Exception:
            sw, sh = 1280, 800

        w = min(w, sw - 80)
        h = min(h, sh - 120)
        x = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
        y = parent.winfo_rooty() + max(0, (parent.winfo_height() - h) // 3)
        x = max(20, min(x, sw - w - 20))
        y = max(20, min(y, sh - h - 40))
        self.geometry(f'{w}x{h}+{x}+{y}')

    # --- сборка ---

    def _build_ui(self) -> None:
        # Footer крепим первым, чтобы он всегда был виден.
        self._build_footer()
        self._build_header()
        self._build_body()

    def _build_footer(self) -> None:
        footer = tk.Frame(self, bg=COLORS['panel'])
        footer.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Frame(footer, height=1, bg=COLORS['border']).pack(fill=tk.X)

        ftr = tk.Frame(footer, bg=COLORS['panel'])
        ftr.pack(fill=tk.X, padx=18, pady=12)
        ttk.Button(ftr, text='Отмена', style='Secondary.TButton',
                   command=self._cancel).pack(side=tk.RIGHT, padx=(6, 0))
        ttk.Button(ftr, text='Сохранить', style='Accent.TButton',
                   command=self._ok).pack(side=tk.RIGHT)

    def _build_header(self) -> None:
        header = tk.Frame(self, bg=COLORS['panel'])
        header.pack(side=tk.TOP, fill=tk.X)

        hdr = tk.Frame(header, bg=COLORS['panel'])
        hdr.pack(fill=tk.X, padx=18, pady=(16, 8))

        tk.Label(hdr, text='Настройки программы',
                 font=FONTS['dialog'], fg=COLORS['text'],
                 bg=COLORS['panel']).pack(anchor='w')

        tk.Label(
            hdr,
            text=('Здесь задаются рабочие пути: где хранить префиксы, '
                  'откуда открывать XML и куда сохранять CSV. '
                  'Файл settings.json всегда лежит в папке, '
                  'указанной ниже - её менять не нужно.'),
            font=FONTS['body_sm'],
            fg=COLORS['text_muted'], bg=COLORS['panel'],
            justify=tk.LEFT, anchor='w', wraplength=660,
        ).pack(anchor='w', fill=tk.X, pady=(4, 0))

        tk.Frame(self, height=1, bg=COLORS['border']).pack(
            side=tk.TOP, fill=tk.X)

    def _build_body(self) -> None:
        body = tk.Frame(self, bg=COLORS['bg'])
        body.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self._canvas = tk.Canvas(body, highlightthickness=0,
                                 bg=COLORS['bg'])
        self._scroll_canvas = self._canvas
        vsb = ttk.Scrollbar(body, orient='vertical',
                            command=self._canvas.yview,
                            style='Cyan.Vertical.TScrollbar')
        self._canvas.configure(yscrollcommand=vsb.set)

        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self._content = tk.Frame(self._canvas, bg=COLORS['bg'])
        self._content_win_id = self._canvas.create_window(
            (0, 0), window=self._content, anchor='nw')

        self._content.bind('<Configure>',
                           lambda e: self._refresh_scrollregion())
        self._canvas.bind('<Configure>', self._on_canvas_configure)

        card = CardFrame(self._content)
        card.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)
        inner = tk.Frame(card, bg=COLORS['panel'])
        inner.pack(fill=tk.BOTH, expand=True, padx=16, pady=14)

        # Информационная строка про расположение settings.json.
        self._add_info_row(inner)

        # Рабочие пути, которые можно менять.
        self._add_row(inner, 'data_dir', 'Папка данных',
                      'Где хранится config_markers.json (список префиксов). '
                      'По умолчанию совпадает с папкой настроек.')
        self._add_row(inner, 'xml_dir', 'Папка XML по умолчанию',
                      'Откуда открывается ConfigDumpInfo.xml. '
                      'Можно оставить пустой - тогда программа запомнит '
                      'последнюю выбранную папку.')
        self._add_row(inner, 'export_dir', 'Папка экспорта по умолчанию',
                      'Куда сохраняются CSV-файлы и откуда берутся файлы '
                      'для объединения. Пусто - последняя выбранная папка.')

        self._bind_wheel_recursive(self._canvas)
        self._bind_wheel_recursive(self._content)

    def _add_info_row(self, parent: tk.Frame) -> None:
        """Пояснение, где физически лежит settings.json."""
        box = tk.Frame(parent, bg=COLORS['panel_alt'],
                       highlightthickness=1,
                       highlightbackground=COLORS['border'])
        box.pack(fill=tk.X, pady=(0, 6))

        inner = tk.Frame(box, bg=COLORS['panel_alt'])
        inner.pack(fill=tk.X, padx=10, pady=8)

        tk.Label(inner, text='Файл настроек:',
                 font=FONTS['kv_key'], fg=COLORS['accent_dark'],
                 bg=COLORS['panel_alt'], anchor='w').pack(anchor='w')

        path = AppPaths.settings_path()
        tk.Label(inner, text=path,
                 font=FONTS['body_sm'], fg=COLORS['text'],
                 bg=COLORS['panel_alt'], anchor='w', justify=tk.LEFT,
                 wraplength=620).pack(anchor='w', fill=tk.X, pady=(2, 0))

        tk.Label(inner,
                 text=('Этот путь менять не нужно: settings.json '
                       'хранится здесь всегда. Переносить его в другую '
                       'папку вручную тоже не обязательно.'),
                 font=FONTS['body_sm'], fg=COLORS['text_muted'],
                 bg=COLORS['panel_alt'], anchor='w', justify=tk.LEFT,
                 wraplength=620).pack(anchor='w', fill=tk.X, pady=(4, 0))

    def _add_row(self, parent: tk.Frame, key: str, title: str,
                 hint: str) -> None:
        """Строка настройки: заголовок, пояснение, поле, кнопки."""
        tk.Label(parent, text=title, font=FONTS['kv_key'],
                 fg=COLORS['accent_dark'], bg=COLORS['panel'],
                 anchor='w').pack(anchor='w', pady=(10, 0))

        tk.Label(parent, text=hint, font=FONTS['body_sm'],
                 fg=COLORS['text_muted'], bg=COLORS['panel'],
                 anchor='w', justify=tk.LEFT,
                 wraplength=620).pack(anchor='w', fill=tk.X)

        row = tk.Frame(parent, bg=COLORS['panel'])
        row.pack(fill=tk.X, pady=(4, 0))

        ttk.Button(row, text='Открыть', style='Small.TButton',
                   width=self.BTN_WIDTH,
                   command=lambda k=key: self._open_typed(self.vars[k].get())
                   ).pack(side=tk.RIGHT, padx=(6, 0))
        ttk.Button(row, text='Обзор...', style='Small.TButton',
                   width=self.BTN_WIDTH,
                   command=lambda k=key: self._pick_dir(k)
                   ).pack(side=tk.RIGHT)

        var = tk.StringVar(value=self._settings.get(key, ''))
        self.vars[key] = var
        tk.Entry(row, textvariable=var, font=FONTS['body'],
                 bg=COLORS['panel'], fg=COLORS['text'],
                 insertbackground=COLORS['accent']
                 ).pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)

    # --- скролл ---

    def _on_canvas_configure(self, event) -> None:
        if self._content_win_id is not None:
            self._canvas.itemconfigure(self._content_win_id,
                                       width=event.width)
        self._refresh_scrollregion()

    def _refresh_scrollregion(self) -> None:
        """Обновляет scrollregion; если содержимое помещается - скрывает."""
        try:
            self._content.update_idletasks()
            bbox = self._canvas.bbox('all')
            if not bbox:
                self._canvas.configure(scrollregion=(0, 0, 0, 0))
                return
            content_h = bbox[3] - bbox[1]
            canvas_h = self._canvas.winfo_height()
            if content_h <= canvas_h:
                self._canvas.configure(scrollregion=(0, 0, 0, 0))
                self._canvas.yview_moveto(0)
            else:
                self._canvas.configure(scrollregion=bbox)
        except Exception:
            pass

    # --- действия ---

    def _open_typed(self, path: str) -> None:
        path = (path or '').strip()
        if path and os.path.isdir(path):
            AppPaths.open_folder(path)
        elif path:
            messagebox.showinfo('Открыть',
                                'Папка не найдена:\n' + path, parent=self)

    def _pick_dir(self, key: str) -> None:
        initial = self.vars[key].get() or os.path.expanduser('~')
        chosen = filedialog.askdirectory(
            parent=self, title='Выберите папку',
            initialdir=initial if os.path.isdir(initial) else None)
        if chosen:
            self.vars[key].set(os.path.abspath(chosen))

    def _ok(self) -> None:
        result: Dict[str, str] = {}
        for k, v in self.vars.items():
            val = (v.get() or '').strip()
            if val:
                val = os.path.abspath(os.path.expanduser(val))
            result[k] = val

        # settings_dir всегда равен дефолтной папке - его не меняем.
        result['settings_dir'] = AppPaths.default_settings_dir()

        self.result = result
        self._cleanup_and_close()

    def _cancel(self) -> None:
        self.result = None
        self._cleanup_and_close()

    def _cleanup_and_close(self) -> None:
        self._unbind_wheel_all()
        try:
            self.destroy()
        except Exception:
            pass