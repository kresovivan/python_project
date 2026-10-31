"""Палитра и шрифты приложения."""

from typing import Dict

# Цвета интерфейса. Все ключи используются в стилях и виджетах.
COLORS: Dict[str, str] = {
    'bg':            '#f0f2f5',
    'panel':         '#ffffff',
    'panel_alt':     '#f7f8fa',
    'border':        '#d9dde3',
    'text':          '#1c1e21',
    'text_muted':    '#6b7280',
    'accent':        '#2e86de',
    'accent_hover':  '#54a0ff',
    'accent_dark':   '#1c6bc2',
    'warn_bg':       '#fff8e1',
    'warn_fg':       '#7a5b00',
    'highlight':     '#fff3cd',
    'pattern_fg':    '#0a8754',
    'scroll_bg':     '#5dade2',
    'scroll_hover':  '#3498db',
    'scroll_press':  '#2874a6',
    'scroll_trough': '#eaf4fb',
    'scroll_border': '#aed6f1',
    'scroll_arrow':  '#1b4f72',
}

# Шрифты Tk. Формат: (family, size, [weight]).
FONTS: Dict[str, tuple] = {
    'h2':       ('Times New Roman', 10, 'bold'),
    'body':     ('Times New Roman', 10),
    'body_sm':  ('Times New Roman', 9),
    'button':   ('Times New Roman', 10),
    'mono':     ('Times New Roman', 11, 'bold'),

    'title':    ('Times New Roman', 16, 'bold'),
    'section':  ('Times New Roman', 13, 'bold'),
    'step_num': ('Times New Roman', 10, 'bold'),
    'kv_key':   ('Times New Roman', 10, 'bold'),
    'dialog':   ('Times New Roman', 12, 'bold'),
    'hint':     ('Times New Roman', 10, 'bold'),
}