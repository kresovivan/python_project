"""Статусы сравнения, палитра и параметры интерфейса."""

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

# Дерево Tkinter не рассчитано на сотни тысяч строк. Ограничение относится
# только к отображению: выгрузка содержит весь результат сравнения.
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
