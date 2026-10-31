"""Настройка ttk-стилей."""

from tkinter import ttk

from ..constants import COLORS, FONTS


def setup_styles(app) -> ttk.Style:
    """Настраивает все ttk-стили приложения и возвращает Style.

    Тема clam используется как база: она позволяет красить кнопки,
    скроллы и заголовки Treeview. У чекбоксов и радиокнопок в clam
    стандартный вид - галочки и точки, если не задавать indicatorcolor.
    """
    style = ttk.Style(app)
    try:
        style.theme_use('clam')
    except Exception:
        pass

    _setup_scrollbars(style)
    _setup_buttons(style)
    _setup_radio_check(style)
    _setup_progressbar(style)
    _setup_treeview(style)
    _setup_combobox(style, app)
    return style


def _setup_scrollbars(style: ttk.Style) -> None:
    for orient in ('Vertical', 'Horizontal'):
        name = f'Cyan.{orient}.TScrollbar'
        style.configure(
            name, gripcount=0,
            background=COLORS['scroll_bg'],
            darkcolor=COLORS['scroll_hover'],
            lightcolor='#85c1e9',
            troughcolor=COLORS['scroll_trough'],
            bordercolor=COLORS['scroll_border'],
            arrowcolor=COLORS['scroll_arrow'],
            relief='flat',
        )
        style.map(
            name,
            background=[('active', COLORS['scroll_hover']),
                        ('pressed', COLORS['scroll_press'])],
        )


def _setup_buttons(style: ttk.Style) -> None:
    style.configure(
        'Accent.TButton', font=FONTS['button'], foreground='white',
        background=COLORS['accent'], borderwidth=0, focusthickness=0,
        padding=(14, 7), relief='flat',
    )
    style.map(
        'Accent.TButton',
        background=[('active', COLORS['accent_hover']),
                    ('pressed', COLORS['accent_dark']),
                    ('disabled', '#a9c4e5')],
        foreground=[('disabled', '#eef3f8')],
    )

    style.configure(
        'Secondary.TButton', font=FONTS['button'],
        foreground=COLORS['text'], background='#e8eaee',
        borderwidth=0, focusthickness=0,
        padding=(14, 7), relief='flat',
    )
    style.map(
        'Secondary.TButton',
        background=[('active', '#d5d8dd'),
                    ('pressed', '#c2c6cc'),
                    ('disabled', '#f1f3f5')],
        foreground=[('disabled', '#a6adb8')],
    )

    style.configure(
        'Small.TButton', font=FONTS['button'],
        foreground=COLORS['text'], background='#e8eaee',
        borderwidth=0, focusthickness=0,
        padding=(10, 4), relief='flat',
    )
    style.map(
        'Small.TButton',
        background=[('active', '#d5d8dd'), ('disabled', '#f1f3f5')],
        foreground=[('disabled', '#a6adb8')],
    )


def _setup_radio_check(style: ttk.Style) -> None:
    """Стандартные радиокнопки и чекбоксы на панели карточки.

    indicatorcolor не задаём - в теме clam это ломает вид.
    """
    style.configure(
        'Card.TRadiobutton',
        font=FONTS['body'], background=COLORS['panel'],
        foreground=COLORS['text'], focuscolor=COLORS['panel'], padding=2,
    )
    style.map(
        'Card.TRadiobutton',
        background=[('active', COLORS['panel']),
                    ('selected', COLORS['panel'])],
        foreground=[('disabled', COLORS['text_muted'])],
    )

    style.configure(
        'Card.TCheckbutton',
        font=FONTS['body'], background=COLORS['panel'],
        foreground=COLORS['text'], focuscolor=COLORS['panel'], padding=2,
    )
    style.map(
        'Card.TCheckbutton',
        background=[('active', COLORS['panel']),
                    ('selected', COLORS['panel'])],
        foreground=[('disabled', COLORS['text_muted'])],
    )


def _setup_progressbar(style: ttk.Style) -> None:
    style.configure(
        'Custom.Horizontal.TProgressbar',
        troughcolor=COLORS['border'], background=COLORS['accent'],
        bordercolor=COLORS['border'], lightcolor=COLORS['accent'],
        darkcolor=COLORS['accent'], thickness=8,
    )


def _setup_treeview(style: ttk.Style) -> None:
    style.configure(
        'Custom.Treeview', font=FONTS['body'], rowheight=26,
        background=COLORS['panel'], fieldbackground=COLORS['panel'],
        foreground=COLORS['text'], borderwidth=0,
    )
    style.map(
        'Custom.Treeview',
        background=[('selected', COLORS['accent'])],
        foreground=[('selected', 'white')],
    )
    style.configure(
        'Custom.Treeview.Heading', font=FONTS['h2'],
        background='#eef1f5', foreground=COLORS['text'],
        relief='flat', padding=(8, 6),
    )
    style.map(
        'Custom.Treeview.Heading',
        background=[('active', '#dde3ea')],
    )


def _setup_combobox(style: ttk.Style, app) -> None:
    style.configure(
        'Card.TCombobox',
        foreground=COLORS['text'], fieldbackground=COLORS['panel'],
        background=COLORS['panel'], arrowcolor=COLORS['accent'],
        bordercolor=COLORS['border'], lightcolor=COLORS['border'],
        darkcolor=COLORS['border'], padding=4,
    )
    style.map(
        'Card.TCombobox',
        fieldbackground=[('readonly', COLORS['panel']),
                         ('disabled', COLORS['panel_alt'])],
        foreground=[('disabled', COLORS['text_muted'])],
        selectbackground=[('readonly', COLORS['panel'])],
        selectforeground=[('readonly', COLORS['text'])],
        arrowcolor=[('disabled', COLORS['text_muted'])],
    )

    app.option_add('*TCombobox*Listbox.font', FONTS['body'])
    app.option_add('*TCombobox*Listbox.background', COLORS['panel'])
    app.option_add('*TCombobox*Listbox.foreground', COLORS['text'])
    app.option_add('*TCombobox*Listbox.selectBackground', COLORS['accent'])
    app.option_add('*TCombobox*Listbox.selectForeground', 'white')