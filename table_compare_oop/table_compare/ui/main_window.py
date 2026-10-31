"""Главное окно: настройка, сравнение и просмотр результата."""

import os
import queue
import threading
import time
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from ..config import *
from ..loader import TableLoader
from ..comparator import TableComparator
from ..statistics import StatisticsAnalyzer
from ..exporter import ReportExporter
from .theme import Theme, CardFrame
from .dialogs import HelpWindow, select_excel_sheets

class MainWindow(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title('Сравнение таблиц (CSV / Excel)')
        self.geometry('1400x1000')
        self.minsize(1200, 850)
        self.configure(bg=COLORS['bg'])

        self.paths: List[str] = []
        self.sheets_by_path: Dict[str, List[str]] = {}
        self.frames: Dict[str, pd.DataFrame] = {}
        self.result_df: Optional[pd.DataFrame] = None
        self.last_stat: Dict[str, int] = {}
        self.last_key_fields: List[str] = []
        self.load_metrics = {}
        self.load_elapsed = 0.0
        self.compare_elapsed = 0.0
        self.detail_stats = {'fields': [], 'files': []}
        self._fields_initialized = False

        # Для каждой подписи запоминаем отступ: по нему пересчитываем
        # перенос строк при изменении ширины окна.
        self._dynamic_wrap_labels: List[Tuple[tk.Label, int]] = []
        self._resize_job = None

        self._ui_q = queue.Queue()
        self._help_window: Optional[HelpWindow] = None

        self.status_var = tk.StringVar(value='Готов. Добавьте файлы.')
        self.progress_var = tk.StringVar(value='')
        self.count_files_var = tk.StringVar(value='Файлов: 0')
        self.speed_var = tk.StringVar(value='')

        self.loader = TableLoader()
        Theme.apply(self)
        self._build_ui()

        # Пересчитываем ширину текстовых подсказок при изменении окна.
        self.bind('<Configure>', self._on_window_configure)
        # После первой раскладки тоже один раз пересчитываем.
        self.after(80, self._update_all_wraplengths)

        self.after(60, self._drain_ui_queue)

    # ----------------------------------------------------------
    def _build_ui(self):
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill=tk.BOTH, expand=True)
        self._settings_content = tk.Frame(self.tabs, bg=COLORS['bg'])
        self._result_content = tk.Frame(self.tabs, bg=COLORS['bg'])
        self.tabs.add(self._settings_content, text='Настройка сравнения')
        self.tabs.add(self._result_content, text='Результат и расхождения')

        self._build_top_panel()
        self._build_hint_bar()
        self._build_key_panel()
        self._build_actions_row()
        self._build_progress_row()
        self._build_fields_panel()
        self._build_status_bar()
        self._build_table_panel(expand=True)

    # ----------------------------------------------------------
    #  Перенос текста в подсказках
    # ----------------------------------------------------------

    def _register_wrap_label(self, label: tk.Label,
                             pad_x: int = 80) -> tk.Label:
        """
        Запоминает подпись, у которой wraplength нужно
        пересчитывать при изменении ширины окна.
        pad_x - сколько пикселей справа занято соседями
        (кнопки, отступы и т. п.).
        """
        self._dynamic_wrap_labels.append((label, pad_x))
        return label

    def _on_window_configure(self, event=None):
        # Реагируем только на изменение собственно окна.
        if event is not None and event.widget is not self:
            return
        # Объединяем частые события изменения размера в один пересчёт.
        if self._resize_job is not None:
            try:
                self.after_cancel(self._resize_job)
            except Exception:
                pass
        self._resize_job = self.after(60, self._update_all_wraplengths)

    def _update_all_wraplengths(self):
        self._resize_job = None
        try:
            total_w = self.winfo_width()
        except Exception:
            return
        if total_w <= 1:
            # Окно ещё не отрисовано, попробуем позже.
            self.after(80, self._update_all_wraplengths)
            return
        for label, pad in self._dynamic_wrap_labels:
            try:
                new_wrap = max(160, total_w - pad)
                label.configure(wraplength=new_wrap)
            except Exception:
                pass

    # --- Шаг 1: файлы ---

    def _build_top_panel(self):
        outer = tk.Frame(self._settings_content, bg=COLORS['bg'])
        outer.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(10, 4))

        card = CardFrame(outer)
        card.pack(fill=tk.X)
        inner = tk.Frame(card, bg=COLORS['panel'])
        inner.pack(fill=tk.X, padx=14, pady=10)

        left = tk.Frame(inner, bg=COLORS['panel'])
        left.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Label(left, text='Шаг 1. Файлы для сравнения',
                 font=FONTS['section'], fg=COLORS['accent_dark'],
                 bg=COLORS['panel'], anchor='w'
                 ).pack(anchor='w')

        hint1 = tk.Label(left,
                         text='Выберите 2 и более файла Excel или CSV. '
                              'Каждый файл это снимок одних и тех же данных.',
                         font=FONTS['body_sm'], fg=COLORS['text_muted'],
                         bg=COLORS['panel'], justify=tk.LEFT, anchor='w',
                         wraplength=900)
        hint1.pack(anchor='w', pady=(2, 0))
        self._register_wrap_label(hint1, pad_x=620)

        right = tk.Frame(inner, bg=COLORS['panel'])
        right.pack(side=tk.RIGHT)

        ttk.Button(right, text='Добавить файлы', style='Accent.TButton',
                   command=self.add_files).pack(side=tk.LEFT)
        ttk.Button(right, text='Очистить', style='Secondary.TButton',
                   command=self.clear_files).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(right, text='Инструкция', style='Secondary.TButton',
                   command=self.open_help).pack(side=tk.LEFT, padx=(6, 0))

        self.files_list = tk.Listbox(card, height=2, font=FONTS['body'],
                                     bg=COLORS['panel'], fg=COLORS['text'],
                                     selectbackground=COLORS['accent'],
                                     selectforeground='white',
                                     bd=0, highlightthickness=0)
        self.files_list.pack(fill=tk.X, padx=14, pady=(0, 4))

        bar = tk.Frame(card, bg=COLORS['panel'])
        bar.pack(fill=tk.X, padx=14, pady=(0, 8))
        tk.Label(bar, textvariable=self.count_files_var,
                 font=FONTS['body_sm'], fg=COLORS['text_muted'],
                 bg=COLORS['panel']).pack(side=tk.RIGHT)

    # --- подсказка ---

    def _build_hint_bar(self):
        outer = tk.Frame(self._settings_content, bg=COLORS['bg'])
        outer.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(0, 4))

        bar = tk.Frame(outer, bg=COLORS['warn_bg'],
                       highlightthickness=1,
                       highlightbackground='#f0d998')
        bar.pack(fill=tk.X)
        inner = tk.Frame(bar, bg=COLORS['warn_bg'])
        inner.pack(fill=tk.X, padx=12, pady=6)

        tk.Label(inner, text='Как сравнивать:', font=FONTS['hint'],
                 fg='#b8860b', bg=COLORS['warn_bg']
                 ).pack(side=tk.LEFT, padx=(0, 8), anchor='n')

        hint = tk.Label(
            inner,
            text=('Выберите столбец, по которому можно найти одну и ту же '
                  'запись в разных файлах, например "Номер". Если одного '
                  'столбца недостаточно, выберите несколько. Затем отметьте '
                  'поля, в которых хотите проверить значения, и нажмите '
                  '"Сравнить". Программа покажет совпадения, отличия и '
                  'записи, для которых не нашлось пары.'),
            font=FONTS['body_sm'], fg=COLORS['warn_fg'],
            bg=COLORS['warn_bg'], justify=tk.LEFT, anchor='w',
            wraplength=1300)
        hint.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._register_wrap_label(hint, pad_x=180)

    # --- Шаг 2: ключ ---

    def _build_key_panel(self):
        outer = tk.Frame(self._settings_content, bg=COLORS['bg'])
        outer.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(0, 4))

        card = CardFrame(outer)
        card.pack(fill=tk.X)
        inner = tk.Frame(card, bg=COLORS['panel'])
        inner.pack(fill=tk.X, padx=14, pady=8)

        tk.Label(inner, text='Шаг 2. Ключ: "имя" строки',
                 font=FONTS['section'], fg=COLORS['accent_dark'],
                 bg=COLORS['panel'], anchor='w'
                 ).pack(anchor='w')

        hint2 = tk.Label(
            inner,
            text=('Ctrl+клик добавляет поле, Shift+клик выделяет '
                  'диапазон. Можно выбрать много полей, получится '
                  'большой составной ключ. Одно и то же поле можно '
                  'дополнительно отметить в Шаге 3 как сравниваемое '
                  'или как дополнительное.'),
            font=FONTS['body_sm'], fg=COLORS['text_muted'],
            bg=COLORS['panel'], justify=tk.LEFT, anchor='w',
            wraplength=1300)
        hint2.pack(anchor='w', pady=(2, 0))
        self._register_wrap_label(hint2, pad_x=80)

        row = tk.Frame(inner, bg=COLORS['panel'])
        row.pack(fill=tk.X, pady=(6, 0))

        self.key_list = ttk.Treeview(row, columns=('field',),
                                     show='headings', height=3,
                                     selectmode='extended',
                                     style='Pick.Treeview')
        self.key_list.heading('field', text='Поле')
        self.key_list.column('field', width=380, anchor='w')
        self.key_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        sb = ttk.Scrollbar(row, orient='vertical',
                           command=self.key_list.yview)
        sb.pack(side=tk.LEFT, fill=tk.Y)
        self.key_list.configure(yscrollcommand=sb.set)

        ttk.Button(row, text='Снять выбор', style='Small.TButton',
                   command=self._clear_key_selection
                   ).pack(side=tk.LEFT, padx=(8, 0), anchor='n')

        self.key_hint = tk.Label(inner, text='', font=FONTS['body_sm'],
                                 fg=COLORS['text_muted'], bg=COLORS['panel'],
                                 anchor='w', justify=tk.LEFT,
                                 wraplength=1300)
        self.key_hint.pack(fill=tk.X, pady=(4, 0))
        self._register_wrap_label(self.key_hint, pad_x=80)

        self.key_list.bind('<<TreeviewSelect>>',
                           lambda e: self._sync_compare_list())

    # --- Шаг 3: поля ---

    def _build_fields_panel(self):
        outer = tk.Frame(self._settings_content, bg=COLORS['bg'])
        outer.pack(side=tk.TOP, fill=tk.BOTH, expand=True,
                   padx=10, pady=(0, 4))

        card = CardFrame(outer)
        card.pack(fill=tk.BOTH, expand=True)
        inner = tk.Frame(card, bg=COLORS['panel'])
        inner.pack(fill=tk.BOTH, expand=True, padx=14, pady=8)

        tk.Label(inner,
                 text='Шаг 3. Сравниваемые и дополнительные поля',
                 font=FONTS['section'], fg=COLORS['accent_dark'],
                 bg=COLORS['panel'], anchor='w'
                 ).pack(anchor='w')

        hint3 = tk.Label(
            inner,
            text=('Сравниваемые поля получают статус по каждому '
                  'сравнению. Дополнительные поля показываются в '
                  'отчёте без статуса. Одно и то же поле не может '
                  'быть сразу и сравниваемым, и дополнительным. '
                  'Ключевые поля из Шага 2 здесь тоже доступны: '
                  'их можно дополнительно вывести в отчёт.'),
            font=FONTS['body_sm'], fg=COLORS['text_muted'],
            bg=COLORS['panel'], justify=tk.LEFT, anchor='w',
            wraplength=1300)
        hint3.pack(anchor='w', pady=(2, 0))
        self._register_wrap_label(hint3, pad_x=80)

        lists_row = tk.Frame(inner, bg=COLORS['panel'])
        lists_row.pack(fill=tk.BOTH, expand=True, pady=(6, 0))

        left = tk.Frame(lists_row, bg=COLORS['panel'])
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(left, text='Сравниваемые поля',
                 font=FONTS['h2'], fg=COLORS['text'],
                 bg=COLORS['panel']).pack(anchor='w')

        lbl_cmp = tk.Label(
            left,
            text='По этим полям считается статус Совпадает, '
                 'Отличается, Нет строки. Флаг расхождения '
                 'строки зависит от всех полей в этом списке.',
            font=FONTS['body_sm'], fg=COLORS['text_muted'],
            bg=COLORS['panel'], anchor='w', justify=tk.LEFT,
            wraplength=620)
        lbl_cmp.pack(anchor='w', pady=(0, 4))
        # Отступ учитывает ширину соседней колонки и разделителя.
        self._register_wrap_label(lbl_cmp, pad_x=760)

        cmp_row = tk.Frame(left, bg=COLORS['panel'])
        cmp_row.pack(fill=tk.BOTH, expand=True)

        self.cmp_list = ttk.Treeview(cmp_row, columns=('field',),
                                     show='headings', height=4,
                                     selectmode='extended',
                                     style='Pick.Treeview')
        self.cmp_list.heading('field', text='Поле')
        self.cmp_list.column('field', width=320, anchor='w')
        self.cmp_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        cmp_sb = ttk.Scrollbar(cmp_row, orient='vertical',
                               command=self.cmp_list.yview)
        cmp_sb.pack(side=tk.LEFT, fill=tk.Y)
        self.cmp_list.configure(yscrollcommand=cmp_sb.set)

        cmp_btns = tk.Frame(cmp_row, bg=COLORS['panel'])
        cmp_btns.pack(side=tk.LEFT, padx=(6, 0), anchor='n')
        ttk.Button(cmp_btns, text='Все', style='Small.TButton',
                   command=self._select_all_cmp).pack(fill=tk.X)
        ttk.Button(cmp_btns, text='Ничего', style='Small.TButton',
                   command=self._clear_cmp_selection
                   ).pack(fill=tk.X, pady=(4, 0))

        right = tk.Frame(lists_row, bg=COLORS['panel'])
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))

        tk.Label(right, text='Дополнительные поля',
                 font=FONTS['h2'], fg=COLORS['text'],
                 bg=COLORS['panel']).pack(anchor='w')

        lbl_extra = tk.Label(
            right,
            text='Попадут в отчёт как есть, без статуса. '
                 'Удобно для контекста. Ключевые поля из Шага 2 '
                 'можно добавить сюда, чтобы увидеть их значения '
                 'по каждому файлу отдельной колонкой.',
            font=FONTS['body_sm'], fg=COLORS['text_muted'],
            bg=COLORS['panel'], anchor='w', justify=tk.LEFT,
            wraplength=620)
        lbl_extra.pack(anchor='w', pady=(0, 4))
        self._register_wrap_label(lbl_extra, pad_x=760)

        extra_row = tk.Frame(right, bg=COLORS['panel'])
        extra_row.pack(fill=tk.BOTH, expand=True)

        self.extra_list = ttk.Treeview(extra_row, columns=('field',),
                                       show='headings', height=4,
                                       selectmode='extended',
                                       style='Pick.Treeview')
        self.extra_list.heading('field', text='Поле')
        self.extra_list.column('field', width=320, anchor='w')
        self.extra_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        extra_sb = ttk.Scrollbar(extra_row, orient='vertical',
                                 command=self.extra_list.yview)
        extra_sb.pack(side=tk.LEFT, fill=tk.Y)
        self.extra_list.configure(yscrollcommand=extra_sb.set)

        extra_btns = tk.Frame(extra_row, bg=COLORS['panel'])
        extra_btns.pack(side=tk.LEFT, padx=(6, 0), anchor='n')
        ttk.Button(extra_btns, text='Все', style='Small.TButton',
                   command=self._select_all_extra).pack(fill=tk.X)
        ttk.Button(extra_btns, text='Ничего', style='Small.TButton',
                   command=self._clear_extra_selection
                   ).pack(fill=tk.X, pady=(4, 0))

        self.cmp_hint = tk.Label(inner, text='', font=FONTS['body_sm'],
                                 fg=COLORS['text_muted'], bg=COLORS['panel'],
                                 anchor='w', justify=tk.LEFT,
                                 wraplength=1300)
        self.cmp_hint.pack(fill=tk.X, pady=(4, 0))
        self._register_wrap_label(self.cmp_hint, pad_x=80)

        self.cmp_list.bind('<<TreeviewSelect>>',
                           lambda e: self._on_cmp_select())
        self.extra_list.bind('<<TreeviewSelect>>',
                             lambda e: self._on_extra_select())

    # --- кнопки ---

    def _build_actions_row(self):
        outer = tk.Frame(self._settings_content, bg=COLORS['bg'])
        outer.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 4))

        card = CardFrame(outer)
        card.pack(fill=tk.X)
        inner = tk.Frame(card, bg=COLORS['panel'])
        inner.pack(fill=tk.X, padx=14, pady=8)

        ttk.Button(inner, text='Сравнить', style='Accent.TButton',
                   command=self.run_compare).pack(side=tk.LEFT)

    # --- прогресс ---

    def _build_progress_row(self):
        outer = tk.Frame(self._settings_content, bg=COLORS['bg'])
        outer.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 4))

        card = CardFrame(outer)
        card.pack(fill=tk.X)
        inner = tk.Frame(card, bg=COLORS['panel'])
        inner.pack(fill=tk.X, padx=14, pady=6)

        self.progress = ttk.Progressbar(
            inner, mode='determinate', maximum=100,
            style='Green.Horizontal.TProgressbar')
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Label(inner, textvariable=self.progress_var,
                 font=FONTS['body_sm'], fg=COLORS['text_muted'],
                 bg=COLORS['panel'], width=44, anchor='e'
                 ).pack(side=tk.LEFT, padx=(8, 0))

    # --- таблица результата ---

    def _build_table_panel(self, expand=True):
        outer = tk.Frame(self._result_content, bg=COLORS['bg'])
        outer.pack(side=tk.TOP, fill=tk.BOTH, expand=expand,
                   padx=10, pady=(0, 4))

        card = CardFrame(outer)
        card.pack(fill=tk.BOTH, expand=True)
        inner = tk.Frame(card, bg=COLORS['panel'])
        inner.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        tk.Label(inner, textvariable=self.speed_var,
                 font=FONTS['body_sm'], fg=COLORS['text_muted'],
                 bg=COLORS['panel'], anchor='w'
                 ).pack(fill=tk.X, pady=(0, 6))

        legend = tk.Frame(inner, bg=COLORS['panel'])
        legend.pack(side=tk.TOP, fill=tk.X, pady=(0, 4))

        def legend_item(color, text):
            box = tk.Label(legend, text='  ', background=color,
                           borderwidth=1, relief='solid')
            box.pack(side=tk.LEFT, padx=(6, 2))
            tk.Label(legend, text=text, font=FONTS['body_sm'],
                     fg=COLORS['text'], bg=COLORS['panel']
                     ).pack(side=tk.LEFT)

        legend_item(COLOR_MATCH, 'Совпадает')
        legend_item(COLOR_DIFF, 'Отличается')
        legend_item(COLOR_MISSING, 'Нет строки')
        ttk.Button(legend, text='Подробная статистика',
                   style='Small.TButton',
                   command=self.show_detail_statistics
                   ).pack(side=tk.LEFT, padx=(12, 0))

        self.export_buttons = []
        for label, fmt in (('Экспорт XLSX', 'xlsx'),
                           ('Экспорт CSV', 'csv'),
                           ('Экспорт HTML', 'html')):
            button = ttk.Button(legend, text=label, style='Small.TButton',
                                state='disabled',
                                command=lambda f=fmt: self.export(f))
            button.pack(side=tk.LEFT, padx=(8, 0))
            self.export_buttons.append(button)

        tk.Label(legend, text='Результат сравнения',
                 font=FONTS['h2'], fg=COLORS['text'],
                 bg=COLORS['panel']).pack(side=tk.RIGHT)

        tree_wrap = tk.Frame(inner, bg=COLORS['panel'])
        tree_wrap.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(tree_wrap, show='headings',
                                 style='Compare.Treeview')
        vsb = ttk.Scrollbar(tree_wrap, orient='vertical',
                            command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_wrap, orient='horizontal',
                            command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        tree_wrap.rowconfigure(0, weight=1)
        tree_wrap.columnconfigure(0, weight=1)

        self.tree.tag_configure(TAG_MATCH, background=COLOR_MATCH,
                                foreground=COLORS['text'])
        self.tree.tag_configure(TAG_DIFF, background=COLOR_DIFF,
                                foreground=COLORS['text'])
        self.tree.tag_configure(TAG_MISSING, background=COLOR_MISSING,
                                foreground=COLORS['text'])

    # --- статус-бар ---

    def _build_status_bar(self):
        outer = tk.Frame(self, bg=COLORS['bg'])
        outer.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(0, 8))

        card = CardFrame(outer)
        card.pack(fill=tk.X)
        inner = tk.Frame(card, bg=COLORS['panel'])
        inner.pack(fill=tk.X, padx=14, pady=6)

        status_lbl = tk.Label(inner, textvariable=self.status_var,
                              font=FONTS['body'], fg=COLORS['text_muted'],
                              bg=COLORS['panel'], anchor='w',
                              justify=tk.LEFT, wraplength=1300)
        status_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._register_wrap_label(status_lbl, pad_x=80)

    # ----------------------------------------------------------
    #  Очередь обновлений
    # ----------------------------------------------------------

    def _post(self, fn):
        self._ui_q.put(fn)

    def _drain_ui_queue(self):
        try:
            while True:
                fn = self._ui_q.get_nowait()
                fn()
        except queue.Empty:
            pass
        self.after(60, self._drain_ui_queue)

    def _set_progress(self, pct, text):
        self.progress['value'] = pct
        self.progress_var.set(text)
        self.update_idletasks()

    # ----------------------------------------------------------
    #  Работа со списками полей
    # ----------------------------------------------------------

    @staticmethod
    def _selected(tree):
        out = []
        for iid in tree.selection():
            vals = tree.item(iid, 'values')
            if vals:
                out.append(vals[0])
        return out

    def _fill_fields(self, tree, fields):
        tree.delete(*tree.get_children())
        for f in fields:
            tree.insert('', 'end', iid=f, values=(f,))

    def _set_selection(self, tree, fields):
        wanted = set(fields)
        tree.selection_remove(*tree.selection())
        to_select = [iid for iid in tree.get_children()
                     if tree.item(iid, 'values')
                     and tree.item(iid, 'values')[0] in wanted]
        if to_select:
            tree.selection_add(*to_select)

    def _clear_key_selection(self):
        self.key_list.selection_remove(*self.key_list.selection())

    def _clear_cmp_selection(self):
        self.cmp_list.selection_remove(*self.cmp_list.selection())

    def _clear_extra_selection(self):
        self.extra_list.selection_remove(*self.extra_list.selection())

    def _select_all_cmp(self):
        iids = self.cmp_list.get_children()
        if iids:
            self.cmp_list.selection_add(*iids)

    def _select_all_extra(self):
        iids = self.extra_list.get_children()
        if iids:
            self.extra_list.selection_add(*iids)

    # ----------------------------------------------------------
    #  Файлы
    # ----------------------------------------------------------

    def add_files(self):
        files = filedialog.askopenfilenames(
            title='Выберите файлы Excel или CSV',
            filetypes=[('Таблицы', '*.csv *.tsv *.txt *.xlsx *.xls *.xlsm'),
                       ('Все файлы', '*.*')])
        if not files:
            return
        selected_paths = []
        selected_sheets = {}
        for path in files:
            if os.path.splitext(path)[1].lower() in ('.xlsx', '.xls', '.xlsm'):
                try:
                    names = self.loader.list_sheets(path)
                except Exception as error:
                    messagebox.showerror('Не удалось открыть Excel',
                                         '{}: {}'.format(os.path.basename(path),
                                                        error))
                    continue
                sheets = (select_excel_sheets(self, path, names)
                          if len(names) > 1 else names)
                if not sheets:
                    continue
                selected_sheets[path] = sheets
            selected_paths.append(path)
        if not selected_paths:
            return
        self.paths = selected_paths
        self.sheets_by_path = selected_sheets
        self.files_list.delete(0, tk.END)
        for p in self.paths:
            description = p
            if p in self.sheets_by_path:
                description += ' [' + ', '.join(self.sheets_by_path[p]) + ']'
            self.files_list.insert(tk.END, description)
        self.count_files_var.set('Файлов: {}'.format(len(self.paths)))
        self._reset_results()
        self.load_async()

    def clear_files(self):
        self.paths = []
        self.sheets_by_path = {}
        self.frames = {}
        self.files_list.delete(0, tk.END)
        self._fill_fields(self.key_list, [])
        self._fill_fields(self.cmp_list, [])
        self._fill_fields(self.extra_list, [])
        self.key_hint.config(text='')
        self.cmp_hint.config(text='')
        self.count_files_var.set('Файлов: 0')
        self._set_progress(0, '')
        self.status_var.set('Готов. Добавьте файлы.')
        self._reset_results()

    def load_async(self):
        total = len(self.paths)
        if total == 0:
            return
        self._set_progress(0, 'Загрузка: 0 из {}'.format(total))

        started = time.perf_counter()
        self.load_metrics = {}

        def cb(done, tot, path, elapsed, rows):
            self.load_metrics[path] = {'seconds': elapsed, 'rows': rows}
            pct = int(done * 100 / tot)
            name = os.path.basename(path)
            speed = rows / elapsed if elapsed else 0
            self._post(lambda d=done, t=tot, p=pct, n=name, v=speed:
                       self._set_progress(
                           p, 'Загрузка: {} из {} - {} ({:,.0f} строк/с)'
                           .format(d, t, n, v)))

        def runner():
            results = self.loader.load_files(
                self.paths, progress_cb=cb,
                sheets_by_path=self.sheets_by_path)
            elapsed = time.perf_counter() - started
            self._post(lambda r=results, s=elapsed: self._on_loaded(r, s))

        threading.Thread(target=runner, daemon=True).start()

    def _on_loaded(self, res, elapsed):
        self.load_elapsed = elapsed
        errors = {p: r for p, r in res.items() if isinstance(r, Exception)}
        self.frames = {p: r for p, r in res.items()
                       if not isinstance(r, Exception)}
        if errors:
            msg = '\n'.join('{}: {}'.format(os.path.basename(p), e)
                            for p, e in errors.items())
            messagebox.showwarning('Не удалось прочитать файлы', msg)

        if len(self.frames) < 2:
            self._set_progress(0, 'Ошибка загрузки')
            messagebox.showerror('Ошибка',
                                 'Нужно минимум 2 успешно прочитанных файла.')
            self._populate_fields()
            return

        self._set_progress(
            100, 'Загружено: {} из {}'.format(len(self.frames), len(self.paths)))
        self._populate_fields()

    # ----------------------------------------------------------
    #  Поля
    # ----------------------------------------------------------

    def _populate_fields(self):
        self._fill_fields(self.key_list, [])
        self._fill_fields(self.cmp_list, [])
        self._fill_fields(self.extra_list, [])
        self.key_hint.config(text='')
        self.cmp_hint.config(text='')
        self._fields_initialized = False
        if not self.frames:
            return

        common = None
        for df in self.frames.values():
            cols = set(str(c).strip() for c in df.columns)
            common = cols if common is None else (common & cols)
        fields = sorted(common or [])
        if not fields:
            messagebox.showerror('Ошибка',
                                 'У выбранных файлов нет общих полей.')
            return

        self._fill_fields(self.key_list, fields)

        candidates = ['guid', 'id', 'uuid', 'key', 'number', 'номер', 'код']
        auto = [f for f in fields if f.lower() in candidates] or [fields[0]]
        self._set_selection(self.key_list, auto)

        self._all_fields = fields
        self._sync_compare_list()

    def _all_non_key_fields(self):
        return list(getattr(self, '_all_fields', []))

    def _sync_compare_list(self):
        prev_cmp = set(self._selected(self.cmp_list))
        prev_extra = set(self._selected(self.extra_list))
        all_fields = self._all_non_key_fields()

        prev_cmp &= set(all_fields)
        prev_extra &= set(all_fields)

        if not self._fields_initialized:
            key_fields = set(self._selected(self.key_list))
            prev_cmp = set(all_fields) - key_fields
            self._fields_initialized = True

        prev_cmp -= prev_extra

        self._fill_fields(self.cmp_list, all_fields)
        self._fill_fields(self.extra_list, all_fields)
        self._set_selection(self.cmp_list, prev_cmp)
        self._set_selection(self.extra_list, prev_extra)

        self._update_key_hint()
        self._update_cmp_hint()

    def _on_cmp_select(self):
        cmp_sel = set(self._selected(self.cmp_list))
        to_remove = [iid for iid in self.extra_list.selection()
                     if self.extra_list.item(iid, 'values')
                     and self.extra_list.item(iid, 'values')[0] in cmp_sel]
        if to_remove:
            self.extra_list.selection_remove(*to_remove)
        self._update_cmp_hint()

    def _on_extra_select(self):
        extra_sel = set(self._selected(self.extra_list))
        to_remove = [iid for iid in self.cmp_list.selection()
                     if self.cmp_list.item(iid, 'values')
                     and self.cmp_list.item(iid, 'values')[0] in extra_sel]
        if to_remove:
            self.cmp_list.selection_remove(*to_remove)
        self._update_cmp_hint()

    def _update_key_hint(self):
        keys = self._selected(self.key_list)
        if not keys:
            self.key_hint.config(
                text='Ключ не выбран. Без ключа нельзя сопоставить строки.',
                fg='#a05000')
        elif len(keys) == 1:
            self.key_hint.config(
                text='Ключ: {}. Строки с одинаковым значением считаются '
                     'одной записью.'.format(keys[0]),
                fg=COLORS['accent_dark'])
        else:
            self.key_hint.config(
                text='Составной ключ из {} полей: {}. Записи совпадают '
                     'только при равенстве всех этих полей.'.format(
                         len(keys), ' + '.join(keys)),
                fg=COLORS['accent_dark'])

    def _update_cmp_hint(self):
        cmps = self._selected(self.cmp_list)
        extras = self._selected(self.extra_list)
        parts = []
        if cmps:
            parts.append('Сравниваются: ' + ', '.join(cmps) + '.')
        else:
            parts.append('Сравниваемые поля не выбраны.')
        if extras:
            parts.append('Дополнительно в отчёт: ' + ', '.join(extras) + '.')
        self.cmp_hint.config(text=' '.join(parts))

    def _reset_results(self):
        self.result_df = None
        self.last_stat = {}
        self.last_key_fields = []
        self.detail_stats = {'fields': [], 'files': []}
        self.speed_var.set('')
        self._fields_initialized = False
        for b in self.export_buttons:
            b.state(['disabled'])
        if hasattr(self, 'tree'):
            self.tree.delete(*self.tree.get_children())
            self.tree['columns'] = []

    # ----------------------------------------------------------
    #  Сравнение
    # ----------------------------------------------------------

    def run_compare(self):
        if len(self.frames) < 2:
            messagebox.showerror('Ошибка', 'Сначала загрузите минимум 2 файла.')
            return

        key_fields = self._selected(self.key_list)
        if not key_fields:
            messagebox.showerror(
                'Шаг 2 не выполнен',
                'Выберите хотя бы одно поле-ключ. Ctrl+клик для нескольких '
                'полей составного ключа.')
            return

        cmp_fields = self._selected(self.cmp_list)
        extra_fields = self._selected(self.extra_list)
        if not cmp_fields and not extra_fields:
            messagebox.showerror(
                'Шаг 3 не выполнен',
                'Отметьте хотя бы одно поле: либо в сравниваемых, '
                'либо в дополнительных.')
            return

        self._set_progress(0, 'Сравнение...')

        def progress_cb(done, total):
            pct = int(done * 100 / total) if total else 100
            self._post(lambda p=pct, d=done, t=total:
                       self._set_progress(
                           p, 'Сравнение: {} из {}'.format(d, t)))

        def work():
            try:
                started = time.perf_counter()
                df, stat = TableComparator(self.frames).compare(
                    key_fields, cmp_fields,
                    extra_fields=extra_fields,
                    progress_cb=progress_cb)
                elapsed = time.perf_counter() - started
                self._post(lambda d=df, s=stat, k=key_fields,
                           cf=cmp_fields, t=elapsed:
                           self._on_compared(d, s, k, cf, t))
            except Exception as e:
                self._post(lambda err=e: self._on_error(err))

        threading.Thread(target=work, daemon=True).start()

    def _on_compared(self, df, stat, key_fields, cmp_fields, elapsed):
        self.result_df = df
        self.compare_elapsed = elapsed
        self.detail_stats = StatisticsAnalyzer(
            df, cmp_fields, list(self.frames)).summarize()
        self.last_stat = stat
        self.last_key_fields = list(key_fields)
        self.tabs.select(self._result_content)

        try:
            self.state('zoomed')
        except tk.TclError:
            pass

        total_rows = sum(len(frame) for frame in self.frames.values())
        self.speed_var.set(
            'Загрузка: {:.2f} с, {:,.0f} строк/с  |  '
            'Сопоставление: {:.2f} с, {:,.0f} строк/с'.format(
                self.load_elapsed,
                total_rows / self.load_elapsed if self.load_elapsed else 0,
                elapsed, len(df) / elapsed if elapsed else 0))
        key_desc = ' + '.join(key_fields)
        self._set_progress(100, 'Готово. Строк: {}'.format(len(df)))
        self.status_var.set('Сравнение завершено. Ключ: {}'.format(key_desc))

        for b in self.export_buttons:
            b.state(['!disabled'])

        cols = list(df.columns)
        self.tree.delete(*self.tree.get_children())
        self.tree['columns'] = cols
        for c in cols:
            self.tree.heading(c, text=c)
            if c == FLAG_COLUMN:
                width = 180
            elif c.endswith(STATUS_SUFFIX):
                width = 170
            else:
                width = 190
            self.tree.column(c, width=width, anchor='w', minwidth=80)

        status_cols = [c for c in cols if c.endswith(STATUS_SUFFIX)]

        # В интерфейсе показываем часть строк, чтобы окно не зависало.
        # В self.result_df остаётся полный результат для экспорта.
        preview = df.head(PREVIEW_MAX_ROWS)
        status_idx = [cols.index(c) for c in status_cols]

        for values in preview.itertuples(index=False, name=None):
            statuses = []
            for idx in status_idx:
                v = values[idx]
                if pd.isna(v):
                    continue
                s = str(v).strip().replace('\ufeff', '')
                if s:
                    statuses.append(s)

            if STATUS_MISSING in statuses:
                tag = TAG_MISSING
            elif STATUS_DIFF in statuses:
                tag = TAG_DIFF
            else:
                tag = TAG_MATCH

            self.tree.insert('', 'end', values=values, tags=(tag,))

        self.tree.update_idletasks()
        if len(df) > PREVIEW_MAX_ROWS:
            self.status_var.set(
                self.status_var.get() +
                ' | В таблице показаны первые {} строк; экспорт содержит все {}.'.format(
                    PREVIEW_MAX_ROWS, len(df)))
        # После заполнения таблицы пересчитываем перенос текста.
        self._update_all_wraplengths()

        # Подробности открываются кнопкой рядом с таблицей результатов.

    def _on_error(self, e):
        self._set_progress(0, 'Ошибка')
        messagebox.showerror('Ошибка сравнения', str(e))

    # ----------------------------------------------------------
    #  Окно статистики
    # ----------------------------------------------------------

    def show_detail_statistics(self):
        if self.result_df is None:
            return
        window = tk.Toplevel(self)
        window.title('Подробная статистика расхождений')
        window.geometry('810x550')
        window.configure(bg=COLORS['bg'])
        tabs = ttk.Notebook(window)
        tabs.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        fields_page = tk.Frame(tabs, bg=COLORS['panel'])
        files_page = tk.Frame(tabs, bg=COLORS['panel'])
        tabs.add(fields_page, text='По полям')
        tabs.add(files_page, text='По файлам и скорости')

        tk.Label(fields_page,
                 text='Сравнение значений в записях, которые есть во всех файлах',
                 font=FONTS['h2'], fg=COLORS['accent_dark'],
                 bg=COLORS['panel'], anchor='w'
                 ).pack(fill=tk.X, padx=8, pady=(8, 2))
        tk.Label(fields_page,
                 text='Одна запись может отличаться сразу в нескольких полях.',
                 font=FONTS['body_sm'], fg=COLORS['text_muted'],
                 bg=COLORS['panel'], anchor='w'
                 ).pack(fill=tk.X, padx=8, pady=(0, 6))
        table = ttk.Treeview(fields_page, show='headings',
                             columns=('field', 'checked', 'match', 'diff', 'rate'))
        for col, title, width in (
                ('field', 'Поле', 260), ('checked', 'Проверено', 105),
                ('match', 'Совпало', 105),
                ('diff', 'Отличается', 115),
                ('rate', 'Совпало, %', 115)):
            table.heading(col, text=title)
            table.column(col, width=width, anchor='w')
        scroll = ttk.Scrollbar(fields_page, orient='vertical',
                               command=table.yview)
        table.configure(yscrollcommand=scroll.set)
        table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        for row in self.detail_stats['fields']:
            total = row['checked']
            table.insert('', 'end', values=(
                row['field'], total, row['match'], row['diff'],
                '{:.1f}'.format(100 * row['match'] / total)
                if total else '-'))

        for row in self.detail_stats['files']:
            path = next((p for p in self.frames
                         if os.path.basename(p) == row['file']), None)
            metric = self.load_metrics.get(path, {})
            seconds = metric.get('seconds', 0)
            speed = metric.get('rows', 0) / seconds if seconds else 0
            for label, value in (
                    (row['file'], ''),
                    ('  Строк загружено', '{:,}'.format(metric.get('rows', 0))),
                    ('  Время загрузки', '{:.2f} с'.format(seconds)),
                    ('  Скорость', '{:,.0f} строк/с'.format(speed))):
                tk.Label(files_page, text='{}    {}'.format(label, value),
                         font=FONTS['body'], fg=COLORS['text'],
                         bg=COLORS['panel'], anchor='w'
                         ).pack(fill=tk.X, padx=15, pady=2)

    # ----------------------------------------------------------
    #  Экспорт
    # ----------------------------------------------------------

    def export(self, fmt):
        if self.result_df is None:
            return
        ext = {'xlsx': '.xlsx', 'csv': '.csv', 'html': '.html'}[fmt]
        path = filedialog.asksaveasfilename(
            defaultextension=ext, filetypes=[(fmt.upper(), '*' + ext)])
        if not path:
            return
        for button in self.export_buttons:
            button.state(['disabled'])
        self._set_progress(0, 'Сохранение {}...'.format(fmt.upper()))

        def on_progress(done, total):
            percent = int(100 * done / total) if total else 100
            self._post(lambda p=percent, d=done, t=total:
                       self._set_progress(
                           p, 'Сохранение: {:,} из {:,} записей'.format(d, t)))

        report = ReportExporter(
            self.result_df, self.last_stat, self.last_key_fields,
            self.detail_stats, self.frames, self.load_metrics,
            self.load_elapsed, self.compare_elapsed,
            progress_cb=on_progress)

        def complete(error=None):
            for button in self.export_buttons:
                button.state(['!disabled'])
            if error is None:
                self._set_progress(100, 'Файл сохранён')
                messagebox.showinfo('Сохранено', path)
            else:
                self._set_progress(0, 'Ошибка сохранения')
                messagebox.showerror('Ошибка сохранения', str(error))

        def worker():
            try:
                report.save(fmt, path)
            except Exception as error:
                self._post(lambda err=error: complete(err))
            else:
                self._post(complete)

        threading.Thread(target=worker, daemon=True).start()

    # ----------------------------------------------------------
    #  Инструкция
    # ----------------------------------------------------------

    def open_help(self, anchor='start'):
        if self._help_window is not None:
            try:
                if self._help_window.winfo_exists():
                    self._help_window.deiconify()
                    self._help_window.lift()
                    self._help_window.focus_force()
                    return
            except tk.TclError:
                pass
        self._help_window = HelpWindow(self, anchor=anchor)
