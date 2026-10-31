"""Редактор списка префиксов кастомных объектов."""

import os
from typing import Callable, Dict, Optional, Sequence

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from ..constants import COLORS, FONTS
from ..storage import AppPaths, MarkersStore
from ..ui.widgets import CardFrame


class MarkersDialog(tk.Toplevel):
    """Просмотр и редактирование списка префиксов."""

    def __init__(self, parent: tk.Misc, markers: Sequence[str],
                 data_dir: str,
                 on_change_dir: Optional[Callable[[str], bool]] = None):
        super().__init__(parent)
        self.title('Префиксы кастомных объектов')
        self.geometry('620x620')
        self.minsize(560, 520)
        self.transient(parent)
        self.grab_set()
        self.configure(bg=COLORS['bg'])

        # result: {'markers': [...], 'data_dir': '...'} / None.
        self.result: Optional[Dict] = None
        self._markers = list(markers)
        self._data_dir = data_dir
        self._on_change_dir = on_change_dir

        self._build_ui()
        self._refresh()

        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 620) // 2
        y = parent.winfo_rooty() + 80
        self.geometry(f'620x620+{max(0, x)}+{max(0, y)}')

        self.entry.focus_set()
        self.bind('<Escape>', lambda *_: self._cancel())

    # --- сборка ---

    def _build_ui(self) -> None:
        card = CardFrame(self)
        card.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        inner = tk.Frame(card, bg=COLORS['panel'])
        inner.pack(fill=tk.BOTH, expand=True, padx=16, pady=14)

        tk.Label(inner, text='Префиксы имён кастомных объектов',
                 font=FONTS['dialog'], fg=COLORS['text'],
                 bg=COLORS['panel']).pack(anchor='w')

        tk.Label(
            inner,
            text=('Объект считается кастомным, если "ИмяОбъекта" '
                  'начинается с одного из префиксов.\n'
                  'Пример: ПЛ_, АБ_, Моё_.'),
            font=FONTS['body_sm'], fg=COLORS['text_muted'],
            bg=COLORS['panel'], justify=tk.LEFT, anchor='w',
            wraplength=560,
        ).pack(anchor='w', fill=tk.X, pady=(4, 8))

        self._build_path_box(inner)
        self._build_add_row(inner)
        self._build_listbox(inner)
        self._build_delete_row(inner)
        self._build_actions(inner)

    def _build_path_box(self, parent: tk.Frame) -> None:
        path_box = tk.Frame(parent, bg=COLORS['panel_alt'],
                            highlightthickness=1,
                            highlightbackground=COLORS['border'])
        path_box.pack(fill=tk.X, pady=(0, 10))

        path_inner = tk.Frame(path_box, bg=COLORS['panel_alt'])
        path_inner.pack(fill=tk.X, padx=10, pady=8)

        tk.Label(path_inner, text='Файл префиксов:',
                 font=FONTS['kv_key'], fg=COLORS['accent_dark'],
                 bg=COLORS['panel_alt'], anchor='w').pack(anchor='w')

        self._path_var = tk.StringVar(
            value=AppPaths.markers_path(self._data_dir))
        tk.Label(path_inner, textvariable=self._path_var,
                 font=FONTS['body_sm'], fg=COLORS['text'],
                 bg=COLORS['panel_alt'], anchor='w', justify=tk.LEFT,
                 wraplength=540).pack(anchor='w', fill=tk.X, pady=(2, 6))

        path_btns = tk.Frame(path_inner, bg=COLORS['panel_alt'])
        path_btns.pack(fill=tk.X)
        ttk.Button(path_btns, text='Открыть папку', style='Small.TButton',
                   command=self._open_folder).pack(side=tk.LEFT)
        ttk.Button(path_btns, text='Изменить путь...', style='Small.TButton',
                   command=self._change_dir).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(path_btns, text='Копировать путь', style='Small.TButton',
                   command=self._copy_path).pack(side=tk.LEFT, padx=(6, 0))

    def _build_add_row(self, parent: tk.Frame) -> None:
        add_row = tk.Frame(parent, bg=COLORS['panel'])
        add_row.pack(fill=tk.X, pady=(0, 8))

        self.entry = tk.Entry(add_row, font=FONTS['body'],
                              bg=COLORS['panel'], fg=COLORS['text'],
                              insertbackground=COLORS['accent'])
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)
        self.entry.bind('<Return>', lambda *_: self._add())

        ttk.Button(add_row, text='Добавить', style='Small.TButton',
                   command=self._add).pack(side=tk.LEFT, padx=(8, 0))

    def _build_listbox(self, parent: tk.Frame) -> None:
        list_wrap = tk.Frame(parent, bg=COLORS['border'])
        list_wrap.pack(fill=tk.BOTH, expand=True)

        self.listbox = tk.Listbox(
            list_wrap, font=FONTS['mono'],
            bg=COLORS['panel'], fg=COLORS['text'],
            selectbackground=COLORS['accent'], selectforeground='white',
            activestyle='none', bd=0, highlightthickness=0,
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True,
                          padx=1, pady=1)

        sb = ttk.Scrollbar(list_wrap, orient='vertical',
                           command=self.listbox.yview,
                           style='Cyan.Vertical.TScrollbar')
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.configure(yscrollcommand=sb.set)

    def _build_delete_row(self, parent: tk.Frame) -> None:
        del_row = tk.Frame(parent, bg=COLORS['panel'])
        del_row.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(del_row, text='Удалить выделенное', style='Small.TButton',
                   command=self._remove_selected).pack(side=tk.LEFT)
        ttk.Button(del_row, text='Очистить всё', style='Small.TButton',
                   command=self._clear).pack(side=tk.LEFT, padx=(8, 0))

    def _build_actions(self, parent: tk.Frame) -> None:
        btns = tk.Frame(parent, bg=COLORS['panel'])
        btns.pack(fill=tk.X, pady=(14, 0))
        ttk.Button(btns, text='Отмена', style='Secondary.TButton',
                   command=self._cancel).pack(side=tk.RIGHT, padx=(6, 0))
        ttk.Button(btns, text='Сохранить', style='Accent.TButton',
                   command=self._ok).pack(side=tk.RIGHT)

    # --- действия ---

    def _open_folder(self) -> None:
        if os.path.isdir(self._data_dir):
            AppPaths.open_folder(self._data_dir)
        else:
            messagebox.showinfo('Открыть папку',
                                'Папка не найдена:\n' + self._data_dir,
                                parent=self)

    def _copy_path(self) -> None:
        try:
            self.clipboard_clear()
            self.clipboard_append(self._path_var.get())
            self.update()
        except tk.TclError:
            pass

    def _change_dir(self) -> None:
        if self._on_change_dir is None:
            return
        chosen = filedialog.askdirectory(
            parent=self, title='Папка для config_markers.json',
            initialdir=(self._data_dir
                        if os.path.isdir(self._data_dir) else None))
        if not chosen:
            return
        chosen = os.path.abspath(chosen)
        try:
            ok = self._on_change_dir(chosen)
        except Exception as e:
            messagebox.showerror('Смена папки',
                                 'Не удалось сменить папку:\n' + str(e),
                                 parent=self)
            return
        if ok:
            self._data_dir = chosen
            self._path_var.set(AppPaths.markers_path(self._data_dir))
            self._markers = MarkersStore(self._data_dir).items
            self._refresh()

    def _refresh(self) -> None:
        self.listbox.delete(0, tk.END)
        for m in self._markers:
            self.listbox.insert(tk.END, m)

    def _add(self) -> None:
        val = self.entry.get().strip()
        if not val:
            return
        if val in self._markers:
            self.entry.delete(0, tk.END)
            return
        self._markers.append(val)
        self.entry.delete(0, tk.END)
        self._refresh()

    def _remove_selected(self) -> None:
        sel = list(self.listbox.curselection())
        if not sel:
            return
        for i in reversed(sel):
            del self._markers[i]
        self._refresh()

    def _clear(self) -> None:
        if messagebox.askyesno('Очистить', 'Удалить все префиксы?',
                               parent=self):
            self._markers = []
            self._refresh()

    def _ok(self) -> None:
        self.result = {
            'markers': list(self._markers),
            'data_dir': self._data_dir,
        }
        self.destroy()

    def _cancel(self) -> None:
        self.result = None
        self.destroy()