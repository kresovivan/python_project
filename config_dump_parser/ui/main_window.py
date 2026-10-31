"""Главное окно приложения."""

import os
import re
import threading
from typing import Dict, List, Optional, Sequence

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from ..constants import (
    BASE_COLUMNS,  # noqa: F401  (реэкспорт для совместимости)
    COLORS,
    CUSTOM_TAG,
    FONTS,
    ONLY_LABELS,
    STD_TAG,
)
from ..core import MetadataRow, QueryCompiler, QueryMatcher, XmlParser
from ..dialogs.export import ExportDialog
from ..dialogs.help import HelpWindow
from ..dialogs.markers import MarkersDialog
from ..dialogs.merge_csv import MergeCsvDialog
from ..dialogs.settings import SettingsDialog
from ..storage import MarkersStore, SettingsStore
from .formatting import fmt_number
from .styles import setup_styles
from .widgets import CardFrame


class MainWindow(tk.Tk):
    """Собирает всё вместе: панель кнопок, поиск, таблицу, статус."""

    def __init__(self):
        super().__init__()
        self.title('Анализ метаданных 1С')
        self.geometry('1450x900')
        self.minsize(900, 600)
        self.configure(bg=COLORS['bg'])

        # --- Состояние ---
        self.rows: List[MetadataRow] = []
        self.columns: List[str] = []
        self.filtered: List[MetadataRow] = []
        self.tree: Optional[ttk.Treeview] = None

        self.settings = SettingsStore()
        self.markers = MarkersStore(self.settings.get('data_dir'))

        self.search_mode_var = tk.StringVar(value='all')
        self.only_label_var = tk.StringVar(value='Все')
        self.search_columns: Dict[str, tk.BooleanVar] = {}
        self.column_checkboxes: List[ttk.Checkbutton] = []
        self._matcher = QueryMatcher(None)
        self.search_entry: Optional[tk.Entry] = None

        self._loading_controls: List[tk.Widget] = []
        self._data_loaded = False
        self._help_window: Optional[HelpWindow] = None

        self._search_settings_outer: Optional[tk.Frame] = None
        self._table_outer: Optional[tk.Frame] = None

        setup_styles(self)
        self._build_ui()
        self._set_data_loaded(False)

    # ------------------------------------------------------------------
    #  Сборка интерфейса
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Собирает главное окно по частям."""
        self._build_top_panel()
        self._build_search_hint()
        self._build_search_settings_panel()
        self._build_table_frame()
        self._build_status_bar()

    # --- верхняя панель ---

    def _build_top_panel(self) -> None:
        outer = tk.Frame(self, bg=COLORS['bg'])
        outer.pack(fill=tk.X, padx=12, pady=(12, 6))
        self._top_panel_outer = outer

        panel = CardFrame(outer)
        panel.pack(fill=tk.X)
        inner = tk.Frame(panel, bg=COLORS['panel'])
        inner.pack(fill=tk.X, padx=16, pady=12)

        self._build_action_buttons(inner)
        self._build_search_block(inner)
        self._build_progress(outer)

    def _build_action_buttons(self, parent: tk.Frame) -> None:
        self.btn_open = ttk.Button(parent, text='Открыть XML',
                                   style='Accent.TButton',
                                   command=self.open_file)
        self.btn_open.pack(side=tk.LEFT)

        self.btn_export = ttk.Button(parent, text='Экспорт в CSV',
                                     style='Secondary.TButton',
                                     command=self.export_csv)
        self.btn_export.pack(side=tk.LEFT, padx=(8, 0))

        self.btn_merge = ttk.Button(parent, text='Объединить CSV',
                                    style='Secondary.TButton',
                                    command=self.open_merge_dialog)
        self.btn_merge.pack(side=tk.LEFT, padx=(8, 0))

        self.btn_markers = ttk.Button(parent, text='Префиксы',
                                      style='Secondary.TButton',
                                      command=self.open_markers_dialog)
        self.btn_markers.pack(side=tk.LEFT, padx=(8, 0))

        self.btn_settings = ttk.Button(parent, text='Настройки',
                                       style='Secondary.TButton',
                                       command=self.open_settings_dialog)
        self.btn_settings.pack(side=tk.LEFT, padx=(8, 0))

        self.btn_help = ttk.Button(
            parent, text='Инструкция', style='Secondary.TButton',
            command=lambda: self.open_user_help(anchor='start'))
        self.btn_help.pack(side=tk.RIGHT)

    def _build_search_block(self, parent: tk.Frame) -> None:
        block = tk.Frame(parent, bg=COLORS['panel'])
        block.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(24, 24))

        self.lbl_search = tk.Label(block, text='Поиск:',
                                   font=FONTS['body'], fg=COLORS['text'],
                                   bg=COLORS['panel'])
        self.lbl_search.pack(side=tk.LEFT, padx=(0, 6))

        self.search_var = tk.StringVar()
        self.search_var.trace_add(
            'write',
            lambda *_: (self.apply_filter(), self._update_search_hint()))

        entry_wrap = tk.Frame(block, bg=COLORS['border'])
        entry_wrap.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.search_entry = tk.Entry(
            entry_wrap, textvariable=self.search_var,
            font=FONTS['body'], bd=0, relief='flat',
            bg=COLORS['panel'], fg=COLORS['text'],
            insertbackground=COLORS['accent'], width=30,
            disabledbackground=COLORS['panel_alt'],
            disabledforeground=COLORS['text_muted'])
        self.search_entry.pack(padx=1, pady=1, ipady=5, fill=tk.X,
                               expand=True)

        self._bind_search_context_menu()
        self._bind_search_shortcuts()

        self.btn_clear_search = ttk.Button(
            block, text='Очистить поиск', style='Secondary.TButton',
            command=self._clear_search)
        self.btn_clear_search.pack(side=tk.LEFT, padx=(8, 0))

        self._loading_controls.extend([
            self.btn_export, self.btn_markers,
            self.search_entry, self.btn_clear_search,
        ])

    def _bind_search_context_menu(self) -> None:
        self._search_menu = tk.Menu(self.search_entry, tearoff=0)
        self._search_menu.add_command(label='Вставить',
                                      command=self._paste_to_search)
        self._search_menu.add_command(label='Копировать',
                                      command=self._copy_from_search)
        self._search_menu.add_command(label='Вырезать',
                                      command=self._cut_from_search)
        self._search_menu.add_separator()
        self._search_menu.add_command(label='Очистить',
                                      command=self._clear_search)

        def _popup(event):
            try:
                self._search_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self._search_menu.grab_release()

        self.search_entry.bind('<Button-3>', _popup)

    def _bind_search_shortcuts(self) -> None:
        for seq in ('<Control-v>', '<Control-V>'):
            self.search_entry.bind(seq, lambda e: self._paste_to_search())
        for seq in ('<Control-c>', '<Control-C>'):
            self.search_entry.bind(seq, lambda e: self._copy_from_search())
        for seq in ('<Control-x>', '<Control-X>'):
            self.search_entry.bind(seq, lambda e: self._cut_from_search())
        for seq in ('<Control-a>', '<Control-A>'):
            self.search_entry.bind(seq, lambda e: self._select_all_search())

    def _build_progress(self, parent: tk.Frame) -> None:
        prog_wrap = tk.Frame(parent, bg=COLORS['bg'])
        prog_wrap.pack(fill=tk.X, pady=(8, 0))

        self.progress = ttk.Progressbar(
            prog_wrap, mode='determinate', maximum=100,
            style='Custom.Horizontal.TProgressbar')
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.progress_var = tk.StringVar(value='')
        tk.Label(prog_wrap, textvariable=self.progress_var,
                 font=FONTS['body_sm'], fg=COLORS['text_muted'],
                 bg=COLORS['bg'], width=24, anchor='e'
                 ).pack(side=tk.LEFT, padx=(8, 0))

    # --- панель полей поиска ---

    def _build_search_settings_panel(self) -> None:
        outer = tk.Frame(self, bg=COLORS['bg'])
        self._search_settings_outer = outer
        outer.pack_forget()

        panel = CardFrame(outer)
        panel.pack(fill=tk.X)
        inner = tk.Frame(panel, bg=COLORS['panel'])
        inner.pack(fill=tk.X, padx=16, pady=10)

        tk.Label(inner, text='Поля поиска', font=FONTS['h2'],
                 fg=COLORS['text'], bg=COLORS['panel']).pack(anchor='w')

        self._build_search_mode_row(inner)
        self._build_columns_frame(inner)
        self._build_only_combo_row(inner)

    def _build_search_mode_row(self, parent: tk.Frame) -> None:
        row = tk.Frame(parent, bg=COLORS['panel'])
        row.pack(fill=tk.X, pady=(8, 0))

        self.rb_all_fields = ttk.Radiobutton(
            row, text='По всем полям',
            variable=self.search_mode_var, value='all',
            style='Card.TRadiobutton',
            command=self._on_search_mode_change)
        self.rb_all_fields.pack(side=tk.LEFT, padx=(0, 16))

        self.rb_selected_fields = ttk.Radiobutton(
            row, text='Только по выбранным',
            variable=self.search_mode_var, value='selected',
            style='Card.TRadiobutton',
            command=self._on_search_mode_change)
        self.rb_selected_fields.pack(side=tk.LEFT)

        self.btn_uncheck_all = ttk.Button(
            row, text='Снять все', style='Small.TButton',
            command=lambda: self._set_all_columns(False))
        self.btn_uncheck_all.pack(side=tk.RIGHT, padx=(4, 0))

        self.btn_check_all = ttk.Button(
            row, text='Отметить все', style='Small.TButton',
            command=lambda: self._set_all_columns(True))
        self.btn_check_all.pack(side=tk.RIGHT)

    def _build_columns_frame(self, parent: tk.Frame) -> None:
        self.columns_frame = tk.Frame(parent, bg=COLORS['panel'])
        self.columns_frame.pack(fill=tk.X, pady=(8, 0))

        tk.Frame(parent, height=1, bg=COLORS['border']
                 ).pack(fill=tk.X, pady=(12, 0))

    def _build_only_combo_row(self, parent: tk.Frame) -> None:
        row = tk.Frame(parent, bg=COLORS['panel'])
        row.pack(fill=tk.X, pady=(10, 0))

        self.lbl_obj = tk.Label(row, text='Признак объекта:',
                                font=FONTS['h2'], fg=COLORS['text'],
                                bg=COLORS['panel'])
        self.lbl_obj.pack(side=tk.LEFT, padx=(0, 10))

        self.only_combo = ttk.Combobox(
            row, textvariable=self.only_label_var,
            values=list(ONLY_LABELS.keys()),
            state='readonly', width=24,
            font=FONTS['body'], style='Card.TCombobox')
        self.only_combo.pack(side=tk.LEFT)
        self.only_combo.bind('<<ComboboxSelected>>',
                             lambda *_: self.apply_filter())

        self._loading_controls.extend([
            self.rb_all_fields, self.rb_selected_fields,
            self.btn_check_all, self.btn_uncheck_all, self.only_combo,
        ])

    # --- подсказка ---

    def _build_search_hint(self) -> None:
        outer = tk.Frame(self, bg=COLORS['bg'])
        outer.pack(fill=tk.X, padx=12, pady=(0, 6),
                   after=self._top_panel_outer)
        self._search_hint_outer = outer
        outer.pack_forget()

        bar = tk.Frame(outer, bg=COLORS['warn_bg'],
                       highlightthickness=1,
                       highlightbackground='#f0d998')
        bar.pack(fill=tk.X)

        inner = tk.Frame(bar, bg=COLORS['warn_bg'])
        inner.pack(fill=tk.X, padx=14, pady=8)

        tk.Label(inner, text='Как искать:', font=FONTS['hint'],
                 fg='#b8860b', bg=COLORS['warn_bg']
                 ).pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(
            inner,
            text=('Пишите слово как обычно - оно найдется везде, где есть.   '
                  'Если нужно точнее, добавьте знаки:   '
                  '^ в начале - "начинается с",   '
                  '$ в конце - "заканчивается на",   '
                  '? вместо одной буквы,   '
                  '* вместо нескольких.'),
            font=FONTS['body'], fg=COLORS['warn_fg'],
            bg=COLORS['warn_bg'], justify=tk.LEFT, anchor='w'
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _update_search_hint(self) -> None:
        if self.search_var.get().strip():
            self._search_hint_outer.pack(fill=tk.X, padx=12, pady=(0, 6),
                                         after=self._top_panel_outer)
        else:
            self._search_hint_outer.pack_forget()

    # --- таблица и статусбар ---

    def _build_table_frame(self) -> None:
        outer = tk.Frame(self, bg=COLORS['bg'])
        outer.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 6))
        self._table_outer = outer

        panel = CardFrame(outer)
        panel.pack(fill=tk.BOTH, expand=True)

        self.table_frame = tk.Frame(panel, bg=COLORS['panel'])
        self.table_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    def _build_status_bar(self) -> None:
        outer = tk.Frame(self, bg=COLORS['bg'])
        outer.pack(fill=tk.X, padx=12, pady=(0, 10))

        panel = CardFrame(outer)
        panel.pack(fill=tk.X)

        inner = tk.Frame(panel, bg=COLORS['panel'])
        inner.pack(fill=tk.X, padx=16, pady=6)

        self.status_var = tk.StringVar(value='Готов. Откройте XML.')
        tk.Label(inner, textvariable=self.status_var,
                 font=FONTS['body'], fg=COLORS['text_muted'],
                 bg=COLORS['panel'], anchor='w', justify=tk.LEFT
                 ).pack(side=tk.LEFT, fill=tk.X, expand=True)

    # ------------------------------------------------------------------
    #  Загружено / не загружено
    # ------------------------------------------------------------------

    def _set_data_loaded(self, loaded: bool) -> None:
        self._data_loaded = loaded

        for w in self._loading_controls:
            try:
                w.state(['!disabled'] if loaded else ['disabled'])
            except Exception:
                try:
                    w.configure(state='normal' if loaded else 'disabled')
                except Exception:
                    pass

        for lbl in (self.lbl_search, self.lbl_obj):
            try:
                lbl.configure(fg=COLORS['text'] if loaded
                              else COLORS['text_muted'])
            except Exception:
                pass

        if loaded:
            self._search_settings_outer.pack(
                fill=tk.X, padx=12, pady=(0, 6), before=self._table_outer)
        else:
            self._search_settings_outer.pack_forget()

        self._update_checkboxes_state()

    # ------------------------------------------------------------------
    #  Чекбоксы колонок
    # ------------------------------------------------------------------

    def _rebuild_column_checkboxes(self) -> None:
        for w in self.columns_frame.winfo_children():
            w.destroy()
        self.search_columns.clear()
        self.column_checkboxes.clear()

        for col in self.columns:
            var = tk.BooleanVar(value=True)
            self.search_columns[col] = var

            cb = ttk.Checkbutton(self.columns_frame, text=col,
                                 variable=var,
                                 style='Card.TCheckbutton',
                                 command=self.apply_filter)
            cb.pack(side=tk.LEFT, padx=(0, 12), pady=2)
            self.column_checkboxes.append(cb)

        self._update_checkboxes_state()

    def _update_checkboxes_state(self) -> None:
        enabled = self._data_loaded and self.search_mode_var.get() == 'selected'

        for cb in self.column_checkboxes:
            cb.state(['!disabled'] if enabled else ['disabled'])

        for btn in (getattr(self, 'btn_check_all', None),
                    getattr(self, 'btn_uncheck_all', None)):
            if btn is not None:
                btn.state(['!disabled'] if enabled else ['disabled'])

    def _set_all_columns(self, value: bool) -> None:
        if not self._data_loaded:
            return
        if self.search_mode_var.get() != 'selected':
            return
        for var in self.search_columns.values():
            var.set(value)
        self.apply_filter()

    def _on_search_mode_change(self) -> None:
        self._update_checkboxes_state()
        self.apply_filter()

    def _active_search_columns(self) -> List[str]:
        if self.search_mode_var.get() == 'all':
            return self.columns
        return [c for c, var in self.search_columns.items() if var.get()]

    # ------------------------------------------------------------------
    #  Инструкция
    # ------------------------------------------------------------------

    def open_user_help(self, anchor: str = 'start') -> None:
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

    # ------------------------------------------------------------------
    #  Буфер обмена в поиске
    # ------------------------------------------------------------------

    def _paste_to_search(self) -> None:
        try:
            text = self.clipboard_get()
        except tk.TclError:
            return
        if not self.search_entry or not self._data_loaded:
            return
        try:
            self.search_entry.delete('sel.first', 'sel.last')
        except tk.TclError:
            pass
        self.search_entry.insert('insert', text)
        self.search_entry.focus_set()

    def _copy_from_search(self) -> None:
        if not self.search_entry:
            return
        try:
            text = self.search_entry.selection_get()
        except tk.TclError:
            return
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()

    def _cut_from_search(self) -> None:
        if not self.search_entry:
            return
        try:
            text = self.search_entry.selection_get()
        except tk.TclError:
            return
        self.clipboard_clear()
        self.clipboard_append(text)
        try:
            self.search_entry.delete('sel.first', 'sel.last')
        except tk.TclError:
            pass
        self.update()

    def _select_all_search(self) -> str:
        if self.search_entry:
            self.search_entry.select_range(0, tk.END)
            self.search_entry.icursor(tk.END)
        return 'break'

    def _clear_search(self) -> None:
        self.search_var.set('')
        if self.search_entry and self._data_loaded:
            self.search_entry.focus_set()

    # ------------------------------------------------------------------
    #  Загрузка XML
    # ------------------------------------------------------------------

    def open_file(self) -> None:
        initial_dir = self.settings.get('xml_dir') or None
        if initial_dir and not os.path.isdir(initial_dir):
            initial_dir = None

        path = filedialog.askopenfilename(
            title='Выберите ConfigDumpInfo.xml',
            filetypes=[('XML files', '*.xml'), ('All files', '*.*')],
            initialdir=initial_dir)
        if not path:
            return

        self.settings.set('xml_dir', os.path.dirname(os.path.abspath(path)))
        try:
            self.settings.save()
        except Exception:
            pass

        self.progress['value'] = 0
        self.progress_var.set('0%')
        self.status_var.set(f'Файл: {os.path.basename(path)}')

        threading.Thread(target=self._worker_parse,
                         args=(path,), daemon=True).start()

    def _worker_parse(self, path: str) -> None:
        """Тело фонового потока: подсчёт + парсинг."""
        try:
            parser = XmlParser(
                path,
                on_count=self._on_count,
                on_progress=self._on_parse_progress,
            )
            rows, cols = parser.run(self.markers)
            self.after(0, lambda: self._after_load(rows, cols))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror('Ошибка', str(e)))
            self.after(0, self._reset_progress)

    # --- колбэки прогресса ---

    def _on_count(self, n: int) -> None:
        self.after(0, lambda: self._update_progress(
            '', f'Подсчёт: {fmt_number(n)}'))

    def _on_parse_progress(self, done: int, total: int) -> None:
        pct = int(done * 100 / total) if total else 100
        text = f'{pct}%  ({fmt_number(done)} из {fmt_number(total)})'
        self.after(0, lambda: self._update_progress(pct, text))

    def _update_progress(self, pct, label: str) -> None:
        if pct != '':
            self.progress['value'] = pct
        self.progress_var.set(label)

    def _reset_progress(self) -> None:
        self.progress.configure(value=0)
        self.progress_var.set('')

    # --- после загрузки ---

    def _after_load(self, rows: List[MetadataRow],
                    cols: List[str]) -> None:
        self.rows = rows
        self.columns = cols

        self.progress['value'] = 100
        self.progress_var.set('100%')

        self._rebuild_table()
        self._rebuild_column_checkboxes()
        self._set_data_loaded(True)

        n_custom = sum(1 for r in self.rows
                       if r.get('ПризнакОбъекта') == CUSTOM_TAG)
        self.status_var.set(
            f'Загружено {fmt_number(len(self.rows))} записей, '
            f'колонок: {len(self.columns)}, '
            f'кастомных: {fmt_number(n_custom)}')

        self.apply_filter()

    # ------------------------------------------------------------------
    #  Таблица
    # ------------------------------------------------------------------

    def _rebuild_table(self) -> None:
        for w in self.table_frame.winfo_children():
            w.destroy()

        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns,
            show='headings', selectmode='browse',
            style='Custom.Treeview')

        for c in self.columns:
            self.tree.heading(c, text=c,
                              command=lambda col=c: self.sort_by(col))
            self.tree.column(c, width=150, anchor='w',
                             minwidth=40, stretch=False)

        for col, w in (('ТипОбъекта', 140), ('ИмяОбъекта', 200),
                       ('ВидЭлемента', 150), ('ИмяЭлемента', 220),
                       ('ВидВложенногоЭлемента', 190),
                       ('ИмяВложенногоЭлемента', 200),
                       ('ПутьЭлемента', 400), ('ПризнакОбъекта', 130),
                       ('name', 400)):
            if col in self.columns:
                self.tree.column(col, width=w)

        vsb = ttk.Scrollbar(self.table_frame, orient='vertical',
                            command=self.tree.yview,
                            style='Cyan.Vertical.TScrollbar')
        hsb = ttk.Scrollbar(self.table_frame, orient='horizontal',
                            command=self.tree.xview,
                            style='Cyan.Horizontal.TScrollbar')

        self.tree.configure(yscrollcommand=vsb.set,
                            xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        self.table_frame.rowconfigure(0, weight=1)
        self.table_frame.columnconfigure(0, weight=1)

        self.tree.tag_configure('odd', background=COLORS['panel'])
        self.tree.tag_configure('even', background=COLORS['panel_alt'])
        self.tree.tag_configure('match', background=COLORS['highlight'])

        self.tree.bind('<Double-Button-1>', self._on_double_click_header)

    def _on_double_click_header(self, event) -> None:
        region = self.tree.identify_region(event.x, event.y)
        if region != 'separator':
            return

        col_id = self.tree.identify_column(event.x)
        if not col_id:
            return
        try:
            col_index = int(col_id[1:]) - 1
        except ValueError:
            return
        if col_index < 0 or col_index >= len(self.columns):
            return

        col_name = self.columns[col_index]
        max_len = len(col_name)
        for r in self.filtered[:2000]:
            v = str(r.get(col_name, ''))
            if len(v) > max_len:
                max_len = len(v)
        self.tree.column(col_name, width=max(60, min(700, max_len * 8)))

    # ------------------------------------------------------------------
    #  Фильтрация и рендеринг
    # ------------------------------------------------------------------

    def apply_filter(self) -> None:
        if not self._data_loaded:
            return

        pattern = self.search_var.get().strip()
        cols = self._active_search_columns()

        self._matcher = QueryMatcher(QueryCompiler.compile(pattern))
        only = ONLY_LABELS.get(self.only_label_var.get(), 'all')

        if (pattern and self.search_mode_var.get() == 'selected'
                and not cols):
            self.filtered = []
            self.status_var.set(
                'Режим "Только по выбранным", но ни одна колонка '
                'не отмечена. Поставьте галочки в панели "Поля поиска".')
            self.render_table()
            return

        if not pattern:
            self.filtered = [r for r in self.rows
                             if self._obj_matches(r, only)]
        else:
            self.filtered = [r for r in self.rows
                             if self._obj_matches(r, only)
                             and self._row_matches(r, cols)]

        self.render_table()

    @staticmethod
    def _obj_matches(row: MetadataRow, only: str) -> bool:
        if only == 'custom':
            return row.get('ПризнакОбъекта') == CUSTOM_TAG
        if only == 'std':
            return row.get('ПризнакОбъекта') == STD_TAG
        return True

    def _row_matches(self, row: MetadataRow, cols: Sequence[str]) -> bool:
        return any(self._matcher.matches(row.get(c, '')) for c in cols)

    def _is_match(self, row: MetadataRow) -> bool:
        if self._matcher.regex is None:
            return False
        return self._row_matches(row, self._active_search_columns())

    def render_table(self) -> None:
        if not self.tree:
            return

        self.tree.delete(*self.tree.get_children())
        for i, r in enumerate(self.filtered):
            is_match = self._is_match(r)
            tags = ['match'] if is_match else ['odd' if i % 2 else 'even']
            self.tree.insert(
                '', tk.END,
                values=tuple(str(r.get(c, '')) for c in self.columns),
                tags=tuple(tags))

        self.status_var.set(
            f'Показано {fmt_number(len(self.filtered))} '
            f'(всего: {fmt_number(len(self.rows))})')

    def sort_by(self, col: str) -> None:
        self.filtered.sort(key=lambda r: str(r.get(col, '')).lower())
        self.render_table()

    # ------------------------------------------------------------------
    #  Префиксы
    # ------------------------------------------------------------------

    def open_markers_dialog(self) -> None:
        dlg = MarkersDialog(self, self.markers.items,
                            self.settings.get('data_dir'),
                            on_change_dir=self._change_data_dir)
        self.wait_window(dlg)
        if dlg.result is None:
            return

        self.settings.set('data_dir', dlg.result['data_dir'])
        try:
            self.settings.save()
        except Exception as e:
            messagebox.showerror('Сохранение',
                                 f'Не удалось сохранить settings.json:\n{e}')

        self.markers.set_items(dlg.result['markers'])
        try:
            self.markers.save()
        except Exception as e:
            messagebox.showerror(
                'Сохранение',
                f'Не удалось сохранить список префиксов:\n{e}')

        self._recompute_markers()
        self.apply_filter()

        n_custom = sum(1 for r in self.rows
                       if r.get('ПризнакОбъекта') == CUSTOM_TAG)
        self.status_var.set(
            f'Префиксов: {len(self.markers.items)}. '
            f'Кастомных строк: {n_custom}')

    def _change_data_dir(self, new_dir: str) -> bool:
        new_dir = os.path.abspath(new_dir)
        try:
            os.makedirs(new_dir, exist_ok=True)
        except OSError as e:
            messagebox.showerror('Смена папки',
                                 f'Не удалось создать папку:\n{e}')
            return False

        try:
            self.markers.save(target_dir=new_dir)
        except Exception as e:
            messagebox.showerror('Смена папки',
                                 f'Не удалось записать префиксы:\n{e}')
            return False

        self.settings.set('data_dir', new_dir)
        try:
            self.settings.save()
        except Exception as e:
            messagebox.showerror('Смена папки',
                                 f'Не удалось сохранить settings.json:\n{e}')
            return False

        self.markers.reload(new_dir)
        return True

    def _recompute_markers(self) -> None:
        for r in self.rows:
            name = r.get('ИмяОбъекта', '')
            r.set('ПризнакОбъекта',
                  CUSTOM_TAG if self.markers.is_custom_name(name)
                  else STD_TAG)

    # ------------------------------------------------------------------
    #  Настройки
    # ------------------------------------------------------------------

    def open_settings_dialog(self) -> None:
        """Открывает окно настроек и применяет изменения."""
        dlg = SettingsDialog(self, self.settings.as_dict())
        self.wait_window(dlg)
        if dlg.result is None:
            return

        old_data_dir = self.settings.get('data_dir')
        new = dlg.result

        # Обновляем словарь настроек. settings_dir не меняем -
        # он всегда указывает на дефолтную папку.
        self.settings.set('data_dir', new.get('data_dir', ''))
        self.settings.set('xml_dir', new.get('xml_dir', ''))
        self.settings.set('export_dir', new.get('export_dir', ''))

        # Если папка данных изменилась - переносим туда файл префиксов.
        new_data_dir = self.settings.get('data_dir')
        if old_data_dir != new_data_dir and new_data_dir:
            try:
                os.makedirs(new_data_dir, exist_ok=True)
                self.markers.save(target_dir=new_data_dir)
            except Exception as e:
                messagebox.showerror(
                    'Настройки',
                    f'Не удалось перенести префиксы в новую папку:\n{e}')

        # Сохраняем settings.json (всегда в дефолтную папку).
        try:
            self.settings.save()
        except Exception as e:
            messagebox.showerror('Настройки',
                                 f'Не удалось сохранить settings.json:\n{e}')
            return

        # Перечитываем префиксы из новой папки данных (если она менялась).
        if old_data_dir != new_data_dir:
            self.markers.reload(new_data_dir)
            self._recompute_markers()
            self.apply_filter()

        self.status_var.set(
            f'Настройки сохранены. Файл: {self.settings.settings_path()}')

    # ------------------------------------------------------------------
    #  Объединение CSV
    # ------------------------------------------------------------------

    def open_merge_dialog(self) -> None:
        initial = self.settings.get('export_dir') or ''
        if initial and not os.path.isdir(initial):
            initial = ''

        dlg = MergeCsvDialog(self, initial_dir=initial)
        self.wait_window(dlg)
        if dlg.result is None:
            return

        r = dlg.result
        messagebox.showinfo(
            'Объединение',
            f'Готово.\n'
            f'Файл: {r["path"]}\n'
            f'Файлов объединено: {r["files"]}\n'
            f'Строк данных: {fmt_number(r["rows"])}\n'
            f'Колонок: {len(r["columns"])}',
            parent=self)

        self.settings.set('export_dir', os.path.dirname(r['path']))
        try:
            self.settings.save()
        except Exception:
            pass

    # ------------------------------------------------------------------
    #  Экспорт в CSV
    # ------------------------------------------------------------------

    def export_csv(self) -> None:
        if not self.rows:
            messagebox.showwarning('Экспорт', 'Сначала загрузите XML.')
            return

        pattern = self.search_var.get().strip()
        has_query = bool(pattern)

        matches = ([r for r in self.filtered if self._is_match(r)]
                   if has_query else [])

        dlg = ExportDialog(self, has_query, len(self.rows), len(matches))
        self.wait_window(dlg)
        if not dlg.result:
            return

        mode = dlg.result
        if mode == 'all':
            data: List[MetadataRow] = self.rows
            name = 'export_all.csv'
        else:
            safe_q = re.sub(r'[^\w\u0400-\u04FF\-]', '_',
                            pattern) or 'result'
            data = matches
            name = f'export_{safe_q}.csv'

        if not data:
            messagebox.showinfo('Экспорт', 'Нет строк для выгрузки.')
            return

        initial_dir = self.settings.get('export_dir') or None
        if initial_dir and not os.path.isdir(initial_dir):
            initial_dir = None

        path = filedialog.asksaveasfilename(
            defaultextension='.csv',
            filetypes=[('CSV', '*.csv')],
            initialfile=name,
            initialdir=initial_dir)
        if not path:
            return

        self.settings.set('export_dir',
                          os.path.dirname(os.path.abspath(path)))
        try:
            self.settings.save()
        except Exception:
            pass

        with open(path, 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.DictWriter(f, fieldnames=self.columns,
                               delimiter=';', extrasaction='ignore')
            w.writeheader()
            for r in data:
                w.writerow(r.data)

        messagebox.showinfo(
            'Экспорт',
            f'Сохранено: {path}\n'
            f'Записей: {fmt_number(len(data))}')


# Импорт csv нужен в конце модуля, чтобы не путать с ядром.
import csv  # noqa: E402