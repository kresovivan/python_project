"""Окна статистики и инструкции."""

import tkinter as tk
from tkinter import ttk
import os

from ..config import COLORS, FONTS
from .theme import CardFrame


def select_excel_sheets(parent, path, sheet_names):
    """Показать список листов и вернуть выбранные в порядке книги."""
    window = tk.Toplevel(parent)
    window.title('Листы Excel')
    window.geometry('480x420')
    window.minsize(380, 300)
    window.transient(parent)
    window.configure(bg=COLORS['panel'])
    result = [None]

    tk.Label(window, text=os.path.basename(path), font=FONTS['section'],
             bg=COLORS['panel'], fg=COLORS['accent_dark'],
             anchor='w').pack(fill=tk.X, padx=16, pady=(14, 5))
    tk.Label(window, text='Выберите листы с одинаковыми столбцами. '
             'Их строки будут загружены как одна таблица.',
             font=FONTS['body_sm'], bg=COLORS['panel'],
             fg=COLORS['text'], anchor='w', justify=tk.LEFT,
             wraplength=440).pack(fill=tk.X, padx=16, pady=(0, 8))

    sheet_list = tk.Listbox(window, selectmode=tk.MULTIPLE,
                            exportselection=False, font=FONTS['body'],
                            height=min(12, len(sheet_names)))
    sheet_list.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 10))
    for index, name in enumerate(sheet_names):
        sheet_list.insert(tk.END, name)
        is_report_summary = (name == 'Сводка' and any(
            other.startswith('Результаты') for other in sheet_names))
        if not is_report_summary:
            sheet_list.selection_set(index)

    def accept():
        selected = [sheet_names[index] for index in sheet_list.curselection()]
        if not selected:
            from tkinter import messagebox
            messagebox.showwarning('Листы Excel', 'Выберите хотя бы один лист.',
                                   parent=window)
            return
        result[0] = selected
        window.destroy()

    buttons = tk.Frame(window, bg=COLORS['panel'])
    buttons.pack(fill=tk.X, padx=16, pady=(0, 12))
    ttk.Button(buttons, text='Загрузить', command=accept).pack(side=tk.RIGHT)
    ttk.Button(buttons, text='Отмена', command=window.destroy).pack(
        side=tk.RIGHT, padx=(0, 8))
    window.protocol('WM_DELETE_WINDOW', window.destroy)
    window.grab_set()
    parent.wait_window(window)
    return result[0]


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
