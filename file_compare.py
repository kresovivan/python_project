"""
Сравнение таблиц CSV / Excel.
Один файл, ничего дополнительно подключать не нужно.
"""

import os
import queue
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import pandas as pd
import numpy as np
import chardet


# ============================================================
#  КОНСТАНТЫ
# ============================================================

STATUS_MATCH = 'Совпадает'
STATUS_DIFF = 'Отличается'
STATUS_MISSING = 'Нет строки'

KEY_SEP = ' | '
STATUS_SUFFIX = '::статус_сверки'

FLAG_COLUMN = 'Флаг расхождения'
FLAG_YES = 'Есть расхождение'
FLAG_NO = 'Нет расхождения'

TAG_MATCH = 'tag_match'
TAG_DIFF = 'tag_diff'
TAG_MISSING = 'tag_missing'

# Tkinter Treeview не предназначен для отображения сотен тысяч строк.
# Полный result_df сохраняется и экспортируется, в окне показывается preview.
PREVIEW_MAX_ROWS = 5000

COLOR_MATCH = '#c8f0c8'
COLOR_DIFF = '#ffcccc'
COLOR_MISSING = '#ff9999'
COLOR_TILE_MUTED = '#f1f3f5'

COLORS = {
    'bg': '#eef2f7',
    'panel': '#ffffff',
    'panel_alt': '#f6f8fb',
    'border': '#d6dde6',
    'text': '#1f2937',
    'text_muted': '#7a8699',
    'accent': '#2c7be5',
    'accent_hover': '#1a68c9',
    'accent_dark': '#134b8f',
    'warn_bg': '#fff6df',
    'warn_fg': '#8a6d1a',
}

FONTS = {
    'body': ('Segoe UI', 10),
    'body_sm': ('Segoe UI', 9),
    'h2': ('Segoe UI', 10, 'bold'),
    'hint': ('Segoe UI', 9, 'bold'),
    'button': ('Segoe UI', 10, 'bold'),
    'dialog': ('Segoe UI', 13, 'bold'),
    'section': ('Segoe UI', 10, 'bold'),
    'title': ('Segoe UI', 15, 'bold'),
    'mono': ('Consolas', 10),
    'kv_key': ('Segoe UI', 10, 'bold'),
    'step_num': ('Segoe UI', 10, 'bold'),
    'big_num': ('Segoe UI', 28, 'bold'),
    'tile_title': ('Segoe UI', 11, 'bold'),
    'tile_sub': ('Segoe UI', 9),
    'table_body': ('Segoe UI', 10),
    'table_head': ('Segoe UI', 10, 'bold'),
}


# ============================================================
#  ЧТЕНИЕ ФАЙЛОВ
# ============================================================

def read_any_file(path: str) -> pd.DataFrame:
    """Чтение CSV/Excel с приоритетом быстрых путей для больших CSV."""
    ext = os.path.splitext(path)[1].lower()
    if ext in ('.xlsx', '.xls', '.xlsm'):
        return pd.read_excel(path, dtype=str)

    # Для CSV не читаем первые 200 КБ дважды через Python-engine.
    # Сначала определяем кодировку, затем разделитель и используем C-engine.
    with open(path, 'rb') as f:
        raw = f.read(200_000)
    enc = chardet.detect(raw).get('encoding') or 'utf-8'

    sample = raw.decode(enc, errors='replace')
    sep = None
    try:
        import csv
        dialect = csv.Sniffer().sniff(sample, delimiters=';,	|,')
        sep = dialect.delimiter
    except Exception:
        # Для типичных русскоязычных выгрузок чаще всего используется ';'.
        for candidate in (';', '	', '|', ','):
            if candidate in sample:
                sep = candidate
                break

    if sep is not None:
        try:
            return pd.read_csv(path, dtype=str, sep=sep,
                               encoding=enc, engine='c')
        except Exception:
            pass

    # Резервный путь для нестандартного CSV.
    return pd.read_csv(path, dtype=str, sep=None,
                       engine='python', encoding=enc)


def load_files(paths: List[str], progress_cb=None) -> Dict[str, object]:
    results: Dict[str, object] = {}
    lock = threading.Lock()
    total = len(paths)
    done = 0

    def worker(p: str):
        try:
            return p, read_any_file(p)
        except Exception as e:
            return p, e

    # Параллельная загрузка ускоряет несколько файлов, но для очень
    # больших файлов слишком много потоков резко увеличивает RAM.
    total_bytes = sum(os.path.getsize(p) for p in paths if os.path.exists(p))
    max_workers = min(4, total or 1)
    if total_bytes >= 500 * 1024 * 1024:
        max_workers = min(2, total or 1)

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = [ex.submit(worker, p) for p in paths]
        for fut in as_completed(futures):
            p, r = fut.result()
            with lock:
                results[p] = r
                done += 1
                if progress_cb:
                    progress_cb(done, total, p)
    return results


# ============================================================
#  СРАВНЕНИЕ
# ============================================================

def compare_frames(frames: Dict[str, pd.DataFrame],
                   key_fields: List[str],
                   compare_fields: List[str],
                   extra_fields: Optional[List[str]] = None,
                   progress_cb=None
                   ) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """Векторное сравнение больших таблиц.

    Дубликаты ключей выравниваются по порядковому номеру внутри ключа.
    В отличие от исходной версии здесь нет ``iterrows()`` и словаря из
    объектов pandas.Series для каждой строки.
    """
    extra_fields = extra_fields or []
    if len(frames) < 2:
        raise ValueError("Нужно минимум 2 файла")
    if not key_fields:
        raise ValueError("Не задан ключ")

    names = list(frames.keys())
    short = {n: os.path.splitext(os.path.basename(n))[0] for n in names}
    needed = list(dict.fromkeys(key_fields + compare_fields + extra_fields))
    index_cols = list(key_fields) + ['__occ__']

    compact: Dict[str, pd.DataFrame] = {}
    index_parts = []
    counts_by_file = {}

    # Читаем/обрабатываем только необходимые столбцы.
    for n in names:
        src = frames[n]
        available = {str(c).strip(): c for c in src.columns}
        missing_keys = [k for k in key_fields if k not in available]
        if missing_keys:
            raise ValueError(
                "Поле-ключ '{}' отсутствует в файле {}".format(
                    missing_keys[0], os.path.basename(n)))

        d = pd.DataFrame(index=src.index)
        for field in needed:
            d[field] = src[available[field]] if field in available else None

        for k in key_fields:
            d[k] = d[k].astype(str).str.strip()

        d['__occ__'] = d.groupby(
            key_fields, sort=False, dropna=False).cumcount()
        compact[n] = d
        index_parts.append(d[index_cols])

        cnt = d.groupby(key_fields, sort=False, dropna=False).size()
        if not isinstance(cnt.index, pd.MultiIndex):
            cnt.index = pd.MultiIndex.from_arrays([cnt.index], names=key_fields)
        counts_by_file[n] = cnt

    # Полный набор ключ + номер дубля. Все операции ниже выполняются
    # средствами pandas, без прохода Python по каждой записи.
    master = pd.concat(index_parts, ignore_index=True).drop_duplicates(
        subset=index_cols, ignore_index=True)
    master = master.sort_values(index_cols, kind='stable').reset_index(drop=True)

    count_df = pd.concat(counts_by_file, axis=1).fillna(0)
    count_df.columns = names
    present_all = count_df.gt(0).all(axis=1)
    max_count = count_df.max(axis=1)

    # Если ключ отсутствует хотя бы в одном файле, исходная логика создаёт
    # только один вариант. Если ключ есть во всех — все варианты дублей.
    key_meta = count_df.copy()
    key_meta['_present_all'] = present_all
    key_meta['_max_count'] = max_count
    key_meta = key_meta.reset_index()[key_fields + ['_present_all', '_max_count']]
    master = master.merge(key_meta, on=key_fields, how='left', sort=False)
    keep = master['_present_all'] | master['__occ__'].eq(0)
    selected = master.loc[keep, index_cols].reset_index(drop=True)
    selected_index = pd.MultiIndex.from_frame(selected[index_cols])
    key_index = pd.MultiIndex.from_frame(selected[key_fields])

    key_labels = selected[key_fields].astype(str).agg(KEY_SEP.join, axis=1)
    result = pd.DataFrame({
        'Ключ': key_labels.to_numpy(),
        FLAG_COLUMN: np.full(len(selected), '', dtype=object),
    })

    compare_arrays: Dict[str, List[np.ndarray]] = {
        f: [] for f in compare_fields
    }
    stat = {STATUS_MATCH: 0, STATUS_DIFF: 0, STATUS_MISSING: 0}

    for n in names:
        d = compact[n].set_index(index_cols, drop=False)
        sa = d.reindex(selected_index)
        occurrence_present = sa['__occ__'].notna().to_numpy()

        # Ключ выводится, если сам ключ есть в файле, даже если для данного
        # номера дубля строки уже нет — это поведение исходной версии.
        key_counts = counts_by_file[n]
        key_present = key_counts.reindex(key_index).fillna(0).to_numpy() > 0
        result[f'{short[n]}::ключ'] = np.where(
            key_present, key_labels.to_numpy(dtype=object), None)

        # Значения последней строки каждого ключа нужны для недостающих
        # вариантов дублей — ровно как в исходной реализации.
        last_values = {}
        for f in list(extra_fields) + list(compare_fields):
            if f not in d.columns:
                last_values[f] = None
                continue
            last = compact[n].groupby(
                key_fields, sort=False, dropna=False)[f].last()
            if not isinstance(last.index, pd.MultiIndex):
                last.index = pd.MultiIndex.from_arrays(
                    [last.index], names=key_fields)
            last_values[f] = last.reindex(key_index).to_numpy(dtype=object)

        for f in extra_fields:
            arr = sa[f].to_numpy(dtype=object)
            arr[pd.isna(arr)] = ''
            missing_occ = ~occurrence_present
            if last_values[f] is not None:
                arr[missing_occ & key_present] = last_values[f][missing_occ & key_present]
            arr[~key_present] = None
            arr = np.array([
                None if v is None else '' if pd.isna(v) else str(v)
                for v in arr
            ], dtype=object)
            result[f'{short[n]}::{f}'] = arr

        for f in compare_fields:
            arr = sa[f].to_numpy(dtype=object)
            arr[pd.isna(arr)] = ''
            missing_occ = ~occurrence_present
            if last_values[f] is not None:
                arr[missing_occ & key_present] = last_values[f][missing_occ & key_present]
            arr[~key_present] = None
            arr = np.array([
                None if v is None else '' if pd.isna(v) else str(v)
                for v in arr
            ], dtype=object)
            compare_arrays[f].append(arr)
            result[f'{short[n]}::{f}'] = arr

    # Статусы по каждому полю — векторно.
    any_missing = np.zeros(len(result), dtype=bool)
    any_diff = np.zeros(len(result), dtype=bool)

    for f in compare_fields:
        arr = np.vstack(compare_arrays[f])
        missing = np.equal(arr, None).any(axis=0)
        diff = np.zeros(len(result), dtype=bool)
        for i in range(1, arr.shape[0]):
            diff |= (arr[i] != arr[0])
        diff &= ~missing

        status = np.full(len(result), STATUS_MATCH, dtype=object)
        status[missing] = STATUS_MISSING
        status[~missing & diff] = STATUS_DIFF
        result[f'{f}{STATUS_SUFFIX}'] = status
        any_missing |= missing
        any_diff |= (~missing & diff)

    if compare_fields:
        result[FLAG_COLUMN] = np.where(
            any_missing | any_diff, FLAG_YES, FLAG_NO)
        stat[STATUS_MISSING] = int(any_missing.sum())
        stat[STATUS_DIFF] = int((~any_missing & any_diff).sum())
        stat[STATUS_MATCH] = int((~any_missing & ~any_diff).sum())

    ordered = ['Ключ', FLAG_COLUMN]
    ordered += [f'{short[n]}::ключ' for n in names]
    ordered += [f'{short[n]}::{f}' for f in extra_fields for n in names]
    ordered += [f'{short[n]}::{f}' for f in compare_fields for n in names]
    ordered += [f'{f}{STATUS_SUFFIX}' for f in compare_fields]
    result = result[ordered]

    if progress_cb:
        progress_cb(len(result), len(result))
    return result, stat


# ============================================================
#  СТИЛИ
# ============================================================

def setup_styles(app) -> ttk.Style:
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


# ============================================================
#  CardFrame
# ============================================================

class CardFrame(tk.Frame):
    def __init__(self, parent, **kwargs):
        kwargs.setdefault('bg', COLORS['panel'])
        kwargs.setdefault('highlightthickness', 1)
        kwargs.setdefault('highlightbackground', COLORS['border'])
        super().__init__(parent, **kwargs)


# ============================================================
#  ОКНО СО СТАТИСТИКОЙ
# ============================================================

class StatisticsWindow(tk.Toplevel):
    """Итоги сравнения: понятные плитки и текстовая сводка."""

    def __init__(self, parent, stat: Dict[str, int], total: int,
                 key_desc: str, files_count: int, fields_count: int,
                 on_export=None):
        super().__init__(parent)
        self.title('Результат сравнения')
        self.transient(parent)
        self.configure(bg=COLORS['bg'])
        self.resizable(False, False)
        self._parent = parent
        self._on_export = on_export

        self._build_body(stat, total, key_desc, files_count, fields_count)
        self._build_footer()

        self.update_idletasks()
        w = 760
        h = self.winfo_reqheight()
        x = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
        y = parent.winfo_rooty() + max(40, (parent.winfo_height() - h) // 3)
        self.geometry('{}x{}+{}+{}'.format(w, h, max(0, x), max(0, y)))

        self.bind('<Escape>', lambda *_: self.destroy())
        self.protocol('WM_DELETE_WINDOW', self.destroy)
        self.grab_set()
        self.focus_set()

    def _build_body(self, stat, total, key_desc, files_count, fields_count):
        card = CardFrame(self)
        card.pack(fill=tk.BOTH, expand=True, padx=16, pady=(16, 8))
        inner = tk.Frame(card, bg=COLORS['panel'])
        inner.pack(fill=tk.BOTH, expand=True, padx=20, pady=18)

        match_n = stat.get(STATUS_MATCH, 0)
        diff_n = stat.get(STATUS_DIFF, 0)
        miss_n = stat.get(STATUS_MISSING, 0)
        problem_n = diff_n + miss_n
        clean = (problem_n == 0)

        title_text = 'Все записи совпадают' if clean else 'Сравнение завершено'
        tk.Label(inner, text=title_text,
                 font=FONTS['title'], fg=COLORS['text'],
                 bg=COLORS['panel']).pack(anchor='w')

        if clean:
            subtitle = ('В обоих файлах все записи одинаковые. '
                        'Различий и пропусков нет.')
        else:
            subtitle = ('Проверено записей: {}. Ниже видно, сколько '
                        'из них совпало, сколько отличается и сколько '
                        'отсутствует в одном из файлов.'.format(total))
        tk.Label(inner, text=subtitle,
                 font=FONTS['body'], fg=COLORS['text_muted'],
                 bg=COLORS['panel'], justify=tk.LEFT, anchor='w',
                 wraplength=680
                 ).pack(anchor='w', pady=(4, 14))

        info = tk.Frame(inner, bg=COLORS['panel_alt'],
                        highlightthickness=1,
                        highlightbackground=COLORS['border'])
        info.pack(fill=tk.X, pady=(0, 14))
        info_inner = tk.Frame(info, bg=COLORS['panel_alt'])
        info_inner.pack(fill=tk.X, padx=12, pady=8)

        def info_row(label, value):
            row = tk.Frame(info_inner, bg=COLORS['panel_alt'])
            row.pack(fill=tk.X, pady=1)
            tk.Label(row, text=label, font=FONTS['body_sm'],
                     fg=COLORS['text_muted'], bg=COLORS['panel_alt'],
                     width=26, anchor='w').pack(side=tk.LEFT)
            tk.Label(row, text=value, font=FONTS['body'],
                     fg=COLORS['text'], bg=COLORS['panel_alt'],
                     anchor='w', justify=tk.LEFT).pack(side=tk.LEFT, fill=tk.X)

        info_row('Ключ сравнения:', key_desc)
        info_row('Файлов загружено:', str(files_count))
        info_row('Сравниваемых полей:', str(fields_count))
        info_row('Строк с расхождением:', str(problem_n))

        tiles = tk.Frame(inner, bg=COLORS['panel'])
        tiles.pack(fill=tk.X, pady=(0, 14))

        self._tile(tiles, 'Совпадает', match_n, COLOR_MATCH,
                   'одинаковые значения во всех файлах')
        self._tile(tiles, 'Отличается', diff_n, COLOR_DIFF,
                   'значения есть во всех файлах, но они разные')
        self._tile(tiles, 'Нет строки', miss_n, COLOR_MISSING,
                   'этой записи нет хотя бы в одном файле')

        if clean:
            summary = ('Итог: все {} записей совпадают. '
                       'Различий и пропусков нет.'.format(total))
            summary_color = COLORS['accent_dark']
        elif miss_n == 0:
            summary = ('Итог: из {} записей {} совпадают, '
                       '{} отличаются. Записей, отсутствующих в файлах, '
                       'нет.'.format(total, match_n, diff_n))
            summary_color = COLORS['text']
        elif diff_n == 0:
            summary = ('Итог: из {} записей {} совпадают, '
                       '{} отсутствуют в одном из файлов. '
                       'Различий в значениях нет.'.format(
                           total, match_n, miss_n))
            summary_color = COLORS['text']
        else:
            summary = ('Итог: из {} записей {} совпадают, '
                       '{} отличаются, {} отсутствуют в одном из файлов.'.format(
                           total, match_n, diff_n, miss_n))
            summary_color = COLORS['text']

        tk.Label(inner, text=summary, font=FONTS['body'],
                 fg=summary_color, bg=COLORS['panel'],
                 anchor='w', justify=tk.LEFT, wraplength=680
                 ).pack(anchor='w')

    def _tile(self, parent, title, value, color, subtitle):
        muted = (value == 0)
        bg = COLOR_TILE_MUTED if muted else color
        title_fg = COLORS['text_muted'] if muted else COLORS['text']
        num_fg = COLORS['text_muted'] if muted else COLORS['text']
        sub_fg = COLORS['text_muted']

        tile = tk.Frame(parent, bg=bg,
                        highlightthickness=1,
                        highlightbackground=COLORS['border'])
        tile.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        box = tk.Frame(tile, bg=bg)
        box.pack(fill=tk.BOTH, expand=True, padx=14, pady=12)

        tk.Label(box, text=str(value), font=FONTS['big_num'],
                 fg=num_fg, bg=bg).pack(anchor='w')
        tk.Label(box, text=title, font=FONTS['tile_title'],
                 fg=title_fg, bg=bg).pack(anchor='w', pady=(2, 0))
        tk.Label(box, text=subtitle, font=FONTS['tile_sub'],
                 fg=sub_fg, bg=bg,
                 justify=tk.LEFT, anchor='w', wraplength=180
                 ).pack(anchor='w', pady=(4, 0))

    def _build_footer(self):
        footer = tk.Frame(self, bg=COLORS['bg'])
        footer.pack(fill=tk.X, padx=16, pady=(0, 16))

        if self._on_export is not None:
            ttk.Button(footer, text='Экспорт XLSX',
                       style='Secondary.TButton',
                       command=lambda: self._on_export('xlsx')
                       ).pack(side=tk.LEFT)
            ttk.Button(footer, text='Экспорт CSV',
                       style='Secondary.TButton',
                       command=lambda: self._on_export('csv')
                       ).pack(side=tk.LEFT, padx=(6, 0))
            ttk.Button(footer, text='Экспорт HTML',
                       style='Secondary.TButton',
                       command=lambda: self._on_export('html')
                       ).pack(side=tk.LEFT, padx=(6, 0))

        ttk.Button(footer, text='Закрыть',
                   style='Accent.TButton',
                   command=self.destroy).pack(side=tk.RIGHT)


# ============================================================
#  ОКНО ИНСТРУКЦИИ
# ============================================================

class HelpWindow(tk.Toplevel):
    def __init__(self, parent, anchor='start'):
        super().__init__(parent)
        self.title('Инструкция')
        self.geometry('960x700')
        self.minsize(680, 460)
        self.transient(parent)
        self.configure(bg=COLORS['bg'])
        self._parent = parent

        self._build_header()
        self._build_body()
        self._build_footer()

        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 960) // 2
        y = parent.winfo_rooty() + 30
        self.geometry('960x700+{}+{}'.format(max(0, x), max(0, y)))

        self.bind('<Escape>', lambda *_: self._close())
        self.protocol('WM_DELETE_WINDOW', self._close)

    def _build_header(self):
        header = tk.Frame(self, bg=COLORS['panel'])
        header.pack(fill=tk.X)
        hdr = tk.Frame(header, bg=COLORS['panel'])
        hdr.pack(fill=tk.X, padx=20, pady=14)

        tk.Label(hdr, text='Инструкция', font=FONTS['title'],
                 fg=COLORS['text'], bg=COLORS['panel']).pack(anchor='w')
        tk.Label(hdr,
                 text='Коротко о том, как сравнивать файлы и как читать '
                      'результат.',
                 font=FONTS['body'], fg=COLORS['text_muted'],
                 bg=COLORS['panel'], justify=tk.LEFT
                 ).pack(anchor='w', pady=(4, 0))
        tk.Frame(self, height=1, bg=COLORS['border']).pack(fill=tk.X)

    def _build_body(self):
        container = tk.Frame(self, bg=COLORS['bg'])
        container.pack(fill=tk.BOTH, expand=True)

        self._canvas = tk.Canvas(container, highlightthickness=0,
                                 bg=COLORS['bg'])
        vsb = ttk.Scrollbar(container, orient='vertical',
                            command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=vsb.set)
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self._content = tk.Frame(self._canvas, bg=COLORS['bg'])
        self._content_win = self._canvas.create_window(
            (0, 0), window=self._content, anchor='nw')

        self._content.bind(
            '<Configure>',
            lambda e: self._canvas.configure(
                scrollregion=self._canvas.bbox('all')))
        self._canvas.bind(
            '<Configure>',
            lambda e: self._canvas.itemconfigure(
                self._content_win, width=e.width))

        self._render_sections()
        self._canvas.bind_all('<MouseWheel>', self._on_wheel)

    def _build_footer(self):
        footer = tk.Frame(self, bg=COLORS['panel'])
        footer.pack(fill=tk.X)
        tk.Frame(footer, height=1, bg=COLORS['border']).pack(fill=tk.X)
        ftr = tk.Frame(footer, bg=COLORS['panel'])
        ftr.pack(fill=tk.X, padx=20, pady=10)
        ttk.Button(ftr, text='Закрыть', style='Secondary.TButton',
                   command=self._close).pack(side=tk.RIGHT)

    def _render_sections(self):
        for title, blocks in SECTIONS:
            self._render_section(title, blocks)

    def _render_section(self, title, blocks):
        outer = tk.Frame(self._content, bg=COLORS['bg'])
        outer.pack(fill=tk.X, padx=16, pady=(14, 4))

        tk.Label(outer, text=title, font=FONTS['section'],
                 fg=COLORS['accent'], bg=COLORS['bg']).pack(anchor='w')
        tk.Frame(outer, height=1, bg=COLORS['border']
                 ).pack(fill=tk.X, pady=(4, 8))

        for block in blocks:
            self._render_block(outer, block)

    def _render_block(self, parent, block):
        btype = block.get('type')
        if btype == 'text':
            tk.Label(parent, text=block.get('text', ''),
                     font=FONTS['body'], fg=COLORS['text'], bg=COLORS['bg'],
                     justify=tk.LEFT, anchor='w', wraplength=860
                     ).pack(anchor='w', fill=tk.X, pady=(0, 6))

        elif btype == 'steps':
            for i, step in enumerate(block.get('items', []), 1):
                row = tk.Frame(parent, bg=COLORS['bg'])
                row.pack(fill=tk.X, pady=2)
                tk.Label(row, text='{}.'.format(i), font=FONTS['step_num'],
                         fg=COLORS['accent'], bg=COLORS['bg'],
                         width=3, anchor='nw').pack(side=tk.LEFT)
                tk.Label(row, text=step, font=FONTS['body'],
                         fg=COLORS['text'], bg=COLORS['bg'],
                         justify=tk.LEFT, anchor='w', wraplength=830
                         ).pack(side=tk.LEFT, fill=tk.X)

        elif btype == 'kv':
            for key, val in block.get('items', []):
                row = CardFrame(parent)
                row.pack(fill=tk.X, pady=2)
                inner = tk.Frame(row, bg=COLORS['panel'])
                inner.pack(fill=tk.X, padx=10, pady=6)
                inner.columnconfigure(0, minsize=180, weight=0)
                inner.columnconfigure(1, weight=1)

                tk.Label(inner, text=key, font=FONTS['kv_key'],
                         fg=COLORS['accent_dark'], bg=COLORS['panel'],
                         anchor='nw', justify=tk.LEFT
                         ).grid(row=0, column=0, sticky='nw', padx=(0, 10))
                tk.Label(inner, text=val, font=FONTS['body'],
                         fg=COLORS['text'], bg=COLORS['panel'],
                         anchor='w', justify=tk.LEFT, wraplength=640
                         ).grid(row=0, column=1, sticky='ew')

    def _on_wheel(self, event):
        try:
            self._canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
        except Exception:
            pass

    def _close(self):
        try:
            self.unbind_all('<MouseWheel>')
        except Exception:
            pass
        try:
            self._parent.focus_set()
        except Exception:
            pass
        self.destroy()


SECTIONS = [
    ('Что делает программа', [
        {'type': 'text',
         'text': ('Сравнивает две и более таблицы (Excel или CSV) построчно '
                  'по общему ключу. Показывает, где значения совпали, '
                  'где различаются, где строки нет в одном из файлов. '
                  'По каждой строке ставит общий флаг расхождения, чтобы '
                  'было удобно фильтровать проблемные записи в Excel. '
                  'Результат выгружается в XLSX, CSV или HTML.')},
    ]),

    ('Как начать', [
        {'type': 'steps', 'items': [
            'Нажмите "Добавить файлы" и выберите 2 и более файла Excel или CSV. '
            'Программа сама определит кодировку и разделитель.',
            'В списке "Ключ" выберите поле или несколько полей, по которым '
            'строки считаются одной записью. Для нескольких полей используйте '
            'Ctrl+клик, получится составной ключ.',
            'В списке "Сравниваемые поля" отметьте поля, значения которых надо '
            'сравнивать. По ним считается статус и формируется флаг '
            'расхождения строки.',
            'В списке "Дополнительные поля" отметьте те, что нужно просто '
            'показать в отчёте. Ключевые поля из Шага 2 здесь тоже доступны: '
            'добавьте их сюда, чтобы увидеть значения по каждому файлу '
            'отдельной колонкой. Одно и то же поле не может быть '
            'одновременно и сравниваемым, и дополнительным.',
            'Нажмите "Сравнить". Окно развернётся на весь экран, '
            'откроется окно с итогами, а строки результата появятся '
            'в таблице ниже.',
            'Экспортируйте результат в XLSX, CSV или HTML. Для больших файлов полный результат сохраняется независимо от ограничения предпросмотра.',
        ]},
    ]),

    ('Три роли полей', [
        {'type': 'text',
         'text': ('В программе у каждого поля отчёта есть одна из трёх '
                  'ролей. Разные роли можно совмещать: одно и то же поле '
                  'может быть и ключом, и сравниваемым, и дополнительным '
                  'одновременно, если так удобно.')},
        {'type': 'kv', 'items': [
            ('Ключ', 'Служит "именем" строки. Строки из разных файлов с '
                     'одинаковым значением ключа считаются одной записью. '
                     'Задаётся в Шаге 2.'),
            ('Сравниваемое', 'По этому полю считается статус Совпадает, '
                             'Отличается или Нет строки и формируется '
                             'флаг расхождения. Задаётся в Шаге 3, '
                             'в списке слева.'),
            ('Дополнительное', 'Просто выводится в отчёт как есть, без '
                               'статуса. Удобно для контекста. Задаётся '
                               'в Шаге 3, в списке справа.'),
        ]},
    ]),

    ('Что такое ключ', [
        {'type': 'text',
         'text': ('Ключ это "имя" строки. Строки из разных файлов с одинаковым '
                  'значением ключа программа считает одной и той же записью. '
                  'Обычно это guid, id или номер. Если ключ составной '
                  '(например guid и номер или даже больше полей), выбирайте '
                  'их все: строки сопоставляются только при совпадении '
                  'всех выбранных полей.')},
        {'type': 'kv', 'items': [
            ('Один ключ', 'Строки сопоставляются по значению одного поля.'),
            ('Составной ключ', 'Строки сопоставляются, только если совпали '
                               'все выбранные поля одновременно.'),
            ('Ключ и сравниваемые поля', 'Это разные роли. Одно и то же '
                                         'поле можно отметить и в ключе, '
                                         'и в сравниваемых. В ключе оно '
                                         'участвует в сопоставлении строк, '
                                         'в сравниваемых даёт свой статус '
                                         'и влияет на флаг расхождения.'),
            ('Ключ и дополнительные поля', 'Поля из ключа можно дополнительно '
                                           'вывести в отчёт отдельными '
                                           'колонками по каждому файлу: '
                                           'для этого отметьте их '
                                           'в "Дополнительных полях".'),
        ]},
    ]),

    ('Флаг расхождения', [
        {'type': 'text',
         'text': ('В отчёте сразу после колонки "Ключ" есть колонка '
                  '"Флаг расхождения". Она помогает быстро отфильтровать '
                  'проблемные записи, не разглядывая статусы по каждому полю.')},
        {'type': 'kv', 'items': [
            ('Есть расхождение', 'Хотя бы одно сравниваемое поле дало статус '
                                 '"Отличается" или "Нет строки".'),
            ('Нет расхождения', 'Все сравниваемые поля дали статус '
                                '"Совпадает".'),
            ('Пусто', 'Сравниваемые поля не выбраны, судить о расхождении '
                      'не по чему.'),
        ]},
        {'type': 'text',
         'text': ('В Excel по колонке "Флаг расхождения" удобно ставить '
                  'автофильтр: выбираете "Есть расхождение", и в таблице '
                  'остаются только записи, где что-то не сошлось.')},
    ]),

    ('Как читать результат', [
        {'type': 'kv', 'items': [
            ('Совпадает', 'Значения поля одинаковые во всех файлах.'),
            ('Отличается', 'Значения есть во всех файлах, но различаются.'),
            ('Нет строки', 'Строки с таким ключом нет хотя бы в одном файле.'),
        ]},
        {'type': 'text',
         'text': ('Статус по каждому сравниваемому полю хранится в колонке '
                  'с суффиксом "::статус_сверки". Цвет всей строки выбирается '
                  'по наиболее серьёзному статусу: Нет строки, Отличается, '
                  'Совпадает.')},
    ]),

    ('Колонки в отчёте', [
        {'type': 'kv', 'items': [
            ('Ключ', 'Склеенное значение составного ключа через разделитель.'),
            ('Флаг расхождения', 'Есть расхождение или Нет расхождения '
                                 'по всей строке.'),
            ('Файл::ключ', 'Тот же ключ в разрезе конкретного файла. '
                           'Пусто, если строки нет в этом файле.'),
            ('Файл::поле', 'Значение поля в конкретном файле. Есть и для '
                           'сравниваемых, и для дополнительных полей.'),
            ('Поле::статус_сверки', 'Совпадает, Отличается или Нет строки '
                                    'для сравниваемого поля.'),
        ]},
    ]),

    ('Цвета в таблице', [
        {'type': 'kv', 'items': [
            ('Зелёный', 'Совпадает.'),
            ('Светло-красный', 'Отличается.'),
            ('Тёмно-красный', 'Нет строки.'),
        ]},
    ]),

    ('Экспорт', [
        {'type': 'text',
         'text': ('XLSX открывается в Excel без настроек. CSV сохраняется '
                  'с разделителем ";" и кодировкой UTF-8 с BOM: Excel и '
                  'LibreOffice открывают его без лишних вопросов и без '
                  'кракозябр. HTML тоже сохраняется в UTF-8 с BOM и с '
                  'явным указанием кодировки, поэтому кириллица '
                  'отображается правильно в любом браузере.')},
    ]),

    ('Полезные детали', [
        {'type': 'steps', 'items': [
            'Ctrl+клик добавляет или снимает отдельное поле в списках выбора.',
            'Shift+клик выделяет диапазон.',
            'Кнопки "Все" и "Ничего" отмечают или снимают сразу весь список.',
            'Одно поле не может быть одновременно сравниваемым и '
            'дополнительным: при выборе в одном списке оно снимается '
            'в другом. Ключ от этого ограничения свободен, его можно '
            'и в ключе, и в сравниваемых, и в дополнительных.',
            'Если сравниваемые поля не выбраны, флаг расхождения пустой, '
            'а в отчёт попадают только ключ и дополнительные поля.',
        ]},
    ]),
]


# ============================================================
#  ГЛАВНОЕ ОКНО
# ============================================================

class MainWindow(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title('Сравнение таблиц (CSV / Excel)')
        self.geometry('1400x1000')
        self.minsize(1200, 850)
        self.configure(bg=COLORS['bg'])

        self.paths: List[str] = []
        self.frames: Dict[str, pd.DataFrame] = {}
        self.result_df: Optional[pd.DataFrame] = None
        self.last_stat: Dict[str, int] = {}
        self.last_key_fields: List[str] = []
        self._fields_initialized = False

        # Пары (label, отступ_справа). Для каждой такой подписи
        # wraplength будет пересчитываться при изменении размера окна.
        self._dynamic_wrap_labels: List[Tuple[tk.Label, int]] = []
        self._resize_job = None

        self._ui_q = queue.Queue()
        self._help_window: Optional[HelpWindow] = None
        self._stats_window: Optional[StatisticsWindow] = None

        self.status_var = tk.StringVar(value='Готов. Добавьте файлы.')
        self.progress_var = tk.StringVar(value='')
        self.count_files_var = tk.StringVar(value='Файлов: 0')

        setup_styles(self)
        self._build_ui()

        # Динамический wraplength: пересчёт при ресайзе окна.
        self.bind('<Configure>', self._on_window_configure)
        # После первой раскладки тоже один раз пересчитываем.
        self.after(80, self._update_all_wraplengths)

        self.after(60, self._drain_ui_queue)

    # ----------------------------------------------------------
    def _build_ui(self):
        # Таблица результата создаётся последней и получает
        # весь оставшийся вертикальный размер окна.
        self._build_top_panel()
        self._build_hint_bar()
        self._build_key_panel()
        self._build_fields_panel()
        self._build_actions_row()
        self._build_progress_row()
        self._build_status_bar()
        self._build_table_panel(expand=True)

    # ----------------------------------------------------------
    #  Динамический wraplength
    # ----------------------------------------------------------

    def _register_wrap_label(self, label: tk.Label,
                             pad_x: int = 80) -> tk.Label:
        """
        Запоминает подпись, у которой wraplength нужно
        пересчитывать при изменении ширины окна.
        pad_x — сколько пикселей справа занято соседями
        (кнопки, отступы и т. п.).
        """
        self._dynamic_wrap_labels.append((label, pad_x))
        return label

    def _on_window_configure(self, event=None):
        # Реагируем только на изменение собственно окна.
        if event is not None and event.widget is not self:
            return
        # Сглаживаем частые события: пересчёт через 60 мс.
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
        outer = tk.Frame(self, bg=COLORS['bg'])
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
        outer = tk.Frame(self, bg=COLORS['bg'])
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
            text=('Порядок работы: выберите ключ в Шаге 2, отметьте '
                  'сравниваемые поля в Шаге 3 и нажмите "Сравнить". '
                  'Ключ и сравниваемые поля это разные роли: одно и то же '
                  'поле можно отметить и там, и там. Если поле в ключе, '
                  'оно используется для сопоставления строк; если оно ещё '
                  'и в сравниваемых, оно появится отдельной колонкой по '
                  'каждому файлу и получит свой статус. В отчёте есть '
                  'колонка "Флаг расхождения" со значениями Есть '
                  'расхождение или Нет расхождения по всей строке.'),
            font=FONTS['body_sm'], fg=COLORS['warn_fg'],
            bg=COLORS['warn_bg'], justify=tk.LEFT, anchor='w',
            wraplength=1300)
        hint.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._register_wrap_label(hint, pad_x=180)

    # --- Шаг 2: ключ ---

    def _build_key_panel(self):
        outer = tk.Frame(self, bg=COLORS['bg'])
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
        outer = tk.Frame(self, bg=COLORS['bg'])
        outer.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(0, 4))

        card = CardFrame(outer)
        card.pack(fill=tk.X)
        inner = tk.Frame(card, bg=COLORS['panel'])
        inner.pack(fill=tk.X, padx=14, pady=8)

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
        lists_row.pack(fill=tk.X, pady=(6, 0))

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
        # pad_x = 760: общий отступ от края окна до этой колонки,
        # оставленное место под вторую колонку и разделитель.
        self._register_wrap_label(lbl_cmp, pad_x=760)

        cmp_row = tk.Frame(left, bg=COLORS['panel'])
        cmp_row.pack(fill=tk.X)

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
        extra_row.pack(fill=tk.X)

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
        outer = tk.Frame(self, bg=COLORS['bg'])
        outer.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(0, 4))

        card = CardFrame(outer)
        card.pack(fill=tk.X)
        inner = tk.Frame(card, bg=COLORS['panel'])
        inner.pack(fill=tk.X, padx=14, pady=8)

        ttk.Button(inner, text='Сравнить', style='Accent.TButton',
                   command=self.run_compare).pack(side=tk.LEFT)

        self.btn_xlsx = ttk.Button(inner, text='Экспорт XLSX',
                                   style='Secondary.TButton',
                                   state='disabled',
                                   command=lambda: self.export('xlsx'))
        self.btn_xlsx.pack(side=tk.LEFT, padx=(6, 0))

        self.btn_csv = ttk.Button(inner, text='Экспорт CSV',
                                  style='Secondary.TButton',
                                  state='disabled',
                                  command=lambda: self.export('csv'))
        self.btn_csv.pack(side=tk.LEFT, padx=(6, 0))

        self.btn_html = ttk.Button(inner, text='Экспорт HTML',
                                   style='Secondary.TButton',
                                   state='disabled',
                                   command=lambda: self.export('html'))
        self.btn_html.pack(side=tk.LEFT, padx=(6, 0))

    # --- прогресс ---

    def _build_progress_row(self):
        outer = tk.Frame(self, bg=COLORS['bg'])
        outer.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(0, 4))

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
        outer = tk.Frame(self, bg=COLORS['bg'])
        outer.pack(side=tk.TOP, fill=tk.BOTH, expand=expand,
                   padx=10, pady=(0, 4))

        card = CardFrame(outer)
        card.pack(fill=tk.BOTH, expand=True)
        inner = tk.Frame(card, bg=COLORS['panel'])
        inner.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

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
    #  Утилиты Treeview
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
        self.paths = list(files)
        self.files_list.delete(0, tk.END)
        for p in self.paths:
            self.files_list.insert(tk.END, p)
        self.count_files_var.set('Файлов: {}'.format(len(self.paths)))
        self._reset_results()
        self.load_async()

    def clear_files(self):
        self.paths = []
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

        def cb(done, tot, path):
            pct = int(done * 100 / tot)
            name = os.path.basename(path)
            self._post(lambda d=done, t=tot, p=pct, n=name:
                       self._set_progress(
                           p, 'Загрузка: {} из {} - {}'.format(d, t, n)))

        def runner():
            results = load_files(self.paths, progress_cb=cb)
            self._post(lambda r=results: self._on_loaded(r))

        threading.Thread(target=runner, daemon=True).start()

    def _on_loaded(self, res):
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
        self._fields_initialized = False
        for b in (self.btn_xlsx, self.btn_csv, self.btn_html):
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
                df, stat = compare_frames(
                    self.frames, key_fields, cmp_fields,
                    extra_fields=extra_fields,
                    progress_cb=progress_cb)
                self._post(lambda d=df, s=stat, k=key_fields,
                           cf=cmp_fields:
                           self._on_compared(d, s, k, cf))
            except Exception as e:
                self._post(lambda err=e: self._on_error(err))

        threading.Thread(target=work, daemon=True).start()

    def _on_compared(self, df, stat, key_fields, cmp_fields):
        self.result_df = df
        self.last_stat = stat
        self.last_key_fields = list(key_fields)

        try:
            self.state('zoomed')
        except tk.TclError:
            pass

        problem_n = stat.get(STATUS_DIFF, 0) + stat.get(STATUS_MISSING, 0)
        key_desc = ' + '.join(key_fields)
        self._set_progress(100, 'Готово. Строк: {}'.format(len(df)))
        self.status_var.set(
            'Ключ: {} | Всего: {} | Совпадает: {} | Отличается: {} | '
            'Нет строки: {} | С расхождением: {}'.format(
                key_desc, len(df),
                stat.get(STATUS_MATCH, 0),
                stat.get(STATUS_DIFF, 0),
                stat.get(STATUS_MISSING, 0),
                problem_n))

        for b in (self.btn_xlsx, self.btn_csv, self.btn_html):
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

        # Важно для больших файлов: не создаём в Tkinter сотни тысяч
        # Treeview-item. Полный DataFrame остаётся в self.result_df и
        # полностью доступен для XLSX/CSV/HTML.
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
        # Обновим подсказку под таблицей на всякий случай.
        self._update_all_wraplengths()

        self.show_statistics(stat, len(df), key_desc,
                             len(self.frames), len(cmp_fields))

    def _on_error(self, e):
        self._set_progress(0, 'Ошибка')
        messagebox.showerror('Ошибка сравнения', str(e))

    # ----------------------------------------------------------
    #  Окно статистики
    # ----------------------------------------------------------

    def show_statistics(self, stat, total, key_desc,
                        files_count, fields_count):
        if self._stats_window is not None:
            try:
                if self._stats_window.winfo_exists():
                    self._stats_window.destroy()
            except tk.TclError:
                pass

        self._stats_window = StatisticsWindow(
            self, stat, total, key_desc, files_count, fields_count,
            on_export=self.export)

    # ----------------------------------------------------------
    #  Экспорт
    # ----------------------------------------------------------

    def export(self, fmt):
        if self.result_df is None:
            return
        ext_map = {'xlsx': '.xlsx', 'csv': '.csv', 'html': '.html'}
        path = filedialog.asksaveasfilename(
            defaultextension=ext_map[fmt],
            filetypes=[(fmt.upper(), '*{}'.format(ext_map[fmt]))])
        if not path:
            return
        try:
            if fmt == 'xlsx':
                self.result_df.to_excel(path, index=False)
            elif fmt == 'csv':
                self.result_df.to_csv(path, index=False, sep=';',
                                      encoding='utf-8-sig')
            else:
                with open(path, 'w', encoding='utf-8-sig') as f:
                    f.write(self._df_to_html(self.result_df))
            messagebox.showinfo('Сохранено', path)
        except Exception as e:
            messagebox.showerror('Ошибка сохранения', str(e))

    @staticmethod
    def _df_to_html(df):
        status_cols = [c for c in df.columns if c.endswith(STATUS_SUFFIX)]
        color = {STATUS_MATCH: COLOR_MATCH,
                 STATUS_DIFF: COLOR_DIFF,
                 STATUS_MISSING: COLOR_MISSING}

        css = (
            '<style>'
            'table{border-collapse:collapse;font-family:sans-serif;font-size:13px}'
            'th,td{border:1px solid #bbb;padding:6px 10px;text-align:left;'
            'vertical-align:top}'
            'th{background:#f0f0f0}'
            '</style>'
        )

        head = ''.join('<th>' + str(c) + '</th>' for c in df.columns)
        body_parts = []
        for _, r in df.iterrows():
            statuses = [str(r[c]).strip() for c in status_cols
                        if not pd.isna(r[c])]
            if STATUS_MISSING in statuses:
                bg = color[STATUS_MISSING]
            elif STATUS_DIFF in statuses:
                bg = color[STATUS_DIFF]
            else:
                bg = color[STATUS_MATCH]
            cells = ''.join(
                '<td>' + ('' if pd.isna(r[c]) else str(r[c])) + '</td>'
                for c in df.columns)
            body_parts.append(
                '<tr style="background:' + bg + '">' + cells + '</tr>')

        return (
            '<!DOCTYPE html><html><head>'
            '<meta charset="utf-8">'
            '<meta http-equiv="Content-Type" '
            'content="text/html; charset=utf-8">'
            + css +
            '</head><body><table><thead><tr>' + head +
            '</tr></thead><tbody>' + ''.join(body_parts) +
            '</tbody></table></body></html>'
        )

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


if __name__ == '__main__':
    app = MainWindow()
    app.mainloop()