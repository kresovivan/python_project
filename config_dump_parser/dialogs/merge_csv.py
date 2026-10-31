"""Окно объединения нескольких CSV в один."""

import os
from typing import Dict, List, Optional, Tuple

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from ..constants import COLORS, DEFAULT_MERGED_NAME, FONTS
from ..core.csv_merge import list_csv_files, merge_csv_files
from ..storage import AppPaths
from ..ui.formatting import human_size
from ..ui.widgets import ScrollableMixin


class MergeCsvDialog(tk.Toplevel, ScrollableMixin):
    """Диалог объединения CSV: папка, список файлов, имя итогового."""

    BTN_WIDTH = 12

    def __init__(self, parent: tk.Misc, initial_dir: str = ''):
        super().__init__(parent)
        self.title('Объединение CSV')
        self.minsize(720, 520)
        self.transient(parent)
        self.grab_set()
        self.configure(bg=COLORS['bg'])

        self.result: Optional[Dict] = None
        self._initial_dir = (
            initial_dir if initial_dir and os.path.isdir(initial_dir)
            else os.path.expanduser('~'))

        # Список пар (путь, BooleanVar) - по одной на файл.
        self._files: List[Tuple[str, tk.BooleanVar]] = []
        self._wheel_widgets = []

        self._canvas: Optional[tk.Canvas] = None
        self._scroll_canvas: Optional[tk.Canvas] = None
        self._list_frame: Optional[tk.Frame] = None
        self._list_win: Optional[int] = None

        self._place_window(parent, 900, 640)
        self._build_ui()
        self._reload_files()

        self.bind('<Escape>', lambda *_: self._cancel())
        self.protocol('WM_DELETE_WINDOW', self._cancel)

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
        ttk.Button(ftr, text='Объединить', style='Accent.TButton',
                   command=self._ok).pack(side=tk.RIGHT)

        tk.Label(ftr, text='Итоговый файл:', font=FONTS['body'],
                 fg=COLORS['text'], bg=COLORS['panel']
                 ).pack(side=tk.LEFT)

        self._out_name_var = tk.StringVar(value=DEFAULT_MERGED_NAME)
        tk.Entry(ftr, textvariable=self._out_name_var,
                 font=FONTS['body'], bg=COLORS['panel'],
                 fg=COLORS['text'], insertbackground=COLORS['accent'],
                 width=36).pack(side=tk.LEFT, padx=(8, 0), ipady=3)

    def _build_header(self) -> None:
        header = tk.Frame(self, bg=COLORS['panel'])
        header.pack(side=tk.TOP, fill=tk.X)

        hdr = tk.Frame(header, bg=COLORS['panel'])
        hdr.pack(fill=tk.X, padx=18, pady=(16, 8))

        tk.Label(hdr, text='Объединение CSV-файлов',
                 font=FONTS['dialog'], fg=COLORS['text'],
                 bg=COLORS['panel']).pack(anchor='w')

        tk.Label(
            hdr,
            text=('Выберите папку, отметьте нужные файлы и укажите '
                  'имя итогового файла. Файлы читаются в UTF-8 с BOM, '
                  'разделитель - ";". Колонки берутся из первого '
                  'файла в списке, пустые файлы пропускаются.'),
            font=FONTS['body_sm'],
            fg=COLORS['text_muted'], bg=COLORS['panel'],
            justify=tk.LEFT, anchor='w', wraplength=820,
        ).pack(anchor='w', fill=tk.X, pady=(4, 0))

        tk.Frame(self, height=1, bg=COLORS['border']).pack(
            side=tk.TOP, fill=tk.X)

    def _build_body(self) -> None:
        body = tk.Frame(self, bg=COLORS['bg'])
        body.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self._build_dir_row(body)
        self._build_bulk_row(body)
        self._build_list(body)

    def _build_dir_row(self, parent: tk.Frame) -> None:
        dir_row = tk.Frame(parent, bg=COLORS['bg'])
        dir_row.pack(fill=tk.X, padx=18, pady=(12, 6))

        tk.Label(dir_row, text='Папка с CSV:', font=FONTS['kv_key'],
                 fg=COLORS['accent_dark'], bg=COLORS['bg']
                 ).pack(side=tk.LEFT, padx=(0, 8))

        self._dir_var = tk.StringVar(value=self._initial_dir)
        tk.Entry(dir_row, textvariable=self._dir_var, font=FONTS['body'],
                 bg=COLORS['panel'], fg=COLORS['text'],
                 insertbackground=COLORS['accent']
                 ).pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)

        ttk.Button(dir_row, text='Обзор...', style='Small.TButton',
                   width=self.BTN_WIDTH,
                   command=self._pick_dir).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(dir_row, text='Обновить', style='Small.TButton',
                   width=self.BTN_WIDTH,
                   command=self._reload_files
                   ).pack(side=tk.LEFT, padx=(4, 0))
        ttk.Button(dir_row, text='Открыть', style='Small.TButton',
                   width=self.BTN_WIDTH,
                   command=self._open_dir
                   ).pack(side=tk.LEFT, padx=(4, 0))

    def _build_bulk_row(self, parent: tk.Frame) -> None:
        bulk = tk.Frame(parent, bg=COLORS['bg'])
        bulk.pack(fill=tk.X, padx=18, pady=(2, 6))

        ttk.Button(bulk, text='Выделить все', style='Small.TButton',
                   command=lambda: self._set_all(True)).pack(side=tk.LEFT)
        ttk.Button(bulk, text='Снять все', style='Small.TButton',
                   command=lambda: self._set_all(False)
                   ).pack(side=tk.LEFT, padx=(6, 0))

        self._count_var = tk.StringVar(value='Файлов: 0')
        tk.Label(bulk, textvariable=self._count_var,
                 font=FONTS['body_sm'], fg=COLORS['text_muted'],
                 bg=COLORS['bg']).pack(side=tk.RIGHT)

    def _build_list(self, parent: tk.Frame) -> None:
        list_wrap = tk.Frame(parent, bg=COLORS['border'])
        list_wrap.pack(fill=tk.BOTH, expand=True, padx=18, pady=(0, 12))

        self._canvas = tk.Canvas(list_wrap, highlightthickness=0,
                                 bg=COLORS['panel'])
        self._scroll_canvas = self._canvas
        vsb = ttk.Scrollbar(list_wrap, orient='vertical',
                            command=self._canvas.yview,
                            style='Cyan.Vertical.TScrollbar')
        self._canvas.configure(yscrollcommand=vsb.set)

        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True,
                          padx=1, pady=1)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self._list_frame = tk.Frame(self._canvas, bg=COLORS['panel'])
        self._list_win = self._canvas.create_window(
            (0, 0), window=self._list_frame, anchor='nw')

        self._list_frame.bind(
            '<Configure>',
            lambda e: self._canvas.configure(
                scrollregion=self._canvas.bbox('all')))
        self._canvas.bind(
            '<Configure>',
            lambda e: self._canvas.itemconfigure(self._list_win,
                                                 width=e.width))

        self._bind_wheel_recursive(self._canvas)
        self._bind_wheel_recursive(self._list_frame)

    # --- файлы ---

    def _pick_dir(self) -> None:
        initial = self._dir_var.get() or os.path.expanduser('~')
        chosen = filedialog.askdirectory(
            parent=self, title='Папка с CSV',
            initialdir=initial if os.path.isdir(initial) else None)
        if chosen:
            self._dir_var.set(os.path.abspath(chosen))
            self._reload_files()

    def _open_dir(self) -> None:
        d = self._dir_var.get()
        if d and os.path.isdir(d):
            AppPaths.open_folder(d)
        else:
            messagebox.showinfo('Открыть папку',
                                'Папка не найдена:\n' + d, parent=self)

    def _reload_files(self) -> None:
        """Перечитывает список CSV-файлов в выбранной папке."""
        self._unbind_wheel_all()

        for w in self._list_frame.winfo_children():
            w.destroy()
        self._files.clear()

        folder = self._dir_var.get()
        paths = list_csv_files(folder)

        if not os.path.isdir(folder):
            self._count_var.set('Файлов: 0 (папка не найдена)')
        else:
            for path in paths:
                self._add_file_row(path, os.path.basename(path))
            self._count_var.set(f'Файлов: {len(self._files)}')

        self._bind_wheel_recursive(self._canvas)
        self._bind_wheel_recursive(self._list_frame)

    def _add_file_row(self, full_path: str, name: str) -> None:
        """Одна строка списка файлов: чекбокс + имя + размер."""
        var = tk.BooleanVar(value=True)
        self._files.append((full_path, var))

        row = tk.Frame(self._list_frame, bg=COLORS['panel'])
        row.pack(fill=tk.X, padx=6, pady=1)

        ttk.Checkbutton(row, text=name, variable=var,
                        style='Card.TCheckbutton'
                        ).pack(side=tk.LEFT, anchor='w')

        try:
            size_txt = human_size(os.path.getsize(full_path))
        except OSError:
            size_txt = ''

        tk.Label(row, text=size_txt, font=FONTS['body_sm'],
                 fg=COLORS['text_muted'], bg=COLORS['panel']
                 ).pack(side=tk.RIGHT)

    def _set_all(self, value: bool) -> None:
        for _, var in self._files:
            var.set(value)

    # --- объединение ---

    def _ok(self) -> None:
        folder = self._dir_var.get()
        if not os.path.isdir(folder):
            messagebox.showerror('Объединение',
                                 'Папка не найдена:\n' + folder,
                                 parent=self)
            return

        selected = [p for p, var in self._files if var.get()]
        if not selected:
            messagebox.showinfo('Объединение',
                                'Не выбрано ни одного файла.',
                                parent=self)
            return

        out_name = (self._out_name_var.get() or '').strip() \
            or DEFAULT_MERGED_NAME
        if not out_name.lower().endswith('.csv'):
            out_name += '.csv'

        out_path = os.path.join(folder, out_name)
        if os.path.exists(out_path) and not messagebox.askyesno(
                'Перезапись',
                f'Файл уже существует:\n{out_path}\nПерезаписать?',
                parent=self):
            return

        try:
            files_count, rows_count, columns = merge_csv_files(
                selected, out_path)
        except Exception as e:
            messagebox.showerror('Ошибка объединения', str(e), parent=self)
            return

        self.result = {
            'path': out_path,
            'files': files_count,
            'rows': rows_count,
            'columns': columns,
        }
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