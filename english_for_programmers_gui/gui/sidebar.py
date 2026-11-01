# =============================================================================
# БОКОВОЕ МЕНЮ - пункты страниц, справка, озвучка, тема оформления
# =============================================================================
#
# Меню ничего не делает само: о нажатиях оно сообщает через функции,
# переданные в конструктор (on_navigate, on_help, on_theme). Так меню
# не зависит от окна App, и его можно переставить или заменить отдельно.

from collections.abc import Callable

import customtkinter as ctk

from core.speech import VOICES
from gui import theme
from gui.voice import VoiceController
from gui.widgets import Box

DARK, LIGHT = "Тёмная", "Светлая"


class Sidebar(Box):
    WIDTH = 210

    def __init__(
        self,
        master,
        pages: list[tuple[str, str]],
        voice: VoiceController,
        on_navigate: Callable[[str], None],
        on_help: Callable[[], None],
        on_theme: Callable[[str], None],
    ):
        """pages - список (ключ страницы, название в меню) в порядке пунктов."""
        super().__init__(master, color=theme.SIDEBAR, width=self.WIDTH)
        # Элементы размещены через pack - отключаем pack_propagate,
        # чтобы ширина меню не зависела от длины подписей.
        self.pack_propagate(False)
        self._voice = voice
        self._buttons: dict[str, ctk.CTkButton] = {}
        # Тонкая линия по правому краю отделяет меню от страниц.
        Box(self, color=theme.BORDER, width=1).pack(side="right", fill="y")

        self._build_logo()
        self._build_navigation(pages, on_navigate)
        bottom = Box(self, color=theme.SIDEBAR)
        bottom.pack(side="bottom", fill="x", padx=14, pady=20)
        self._build_help(bottom, on_help)
        self._build_voice(bottom)
        self._build_theme(bottom, on_theme)

    # --- построение ------------------------------------------------------------

    def _build_logo(self) -> None:
        ctk.CTkLabel(self, text="English", font=(theme.DISPLAY, 24), text_color=theme.TEXT).pack(
            anchor="w", padx=24, pady=(28, 0)
        )
        ctk.CTkLabel(self, text="FOR PROGRAMMERS", font=theme.LABEL, text_color=theme.ACCENT).pack(
            anchor="w", padx=25, pady=(0, 26)
        )

    def _build_navigation(self, pages: list[tuple[str, str]], on_navigate: Callable[[str], None]) -> None:
        for number, (key, title) in enumerate(pages, start=1):
            button = ctk.CTkButton(
                self,
                # Номер перед названием подсказывает горячую клавишу: Ctrl + номер.
                text=f"{number:02d}    {title}",
                anchor="w",
                height=40,
                corner_radius=10,
                font=theme.BODY,
                fg_color="transparent",
                hover_color=theme.ACCENT_SOFT,
                text_color=theme.TEXT,
                command=lambda k=key: on_navigate(k),
            )
            button.pack(fill="x", padx=14, pady=2)
            self._buttons[key] = button
        ctk.CTkLabel(
            self, text="CTRL + НОМЕР:\nОТКРЫТЬ ПУНКТ", font=theme.LABEL, text_color=theme.FAINT, justify="left"
        ).pack(anchor="w", padx=28, pady=(8, 0))

    def _build_help(self, parent, on_help: Callable[[], None]) -> None:
        ctk.CTkButton(
            parent,
            text="F1  /  ГОРЯЧИЕ КЛАВИШИ",
            height=32,
            corner_radius=16,
            font=theme.LABEL,
            fg_color="transparent",
            hover_color=theme.ACCENT_SOFT,
            text_color=theme.MUTED,
            border_width=1,
            border_color=theme.LINE_STRONG,
            command=on_help,
        ).pack(fill="x", pady=(0, 14))

    def _build_voice(self, parent) -> None:
        self.auto_speak = ctk.CTkSwitch(
            parent,
            text="Произносить сразу",
            font=theme.SMALL,
            text_color=theme.TEXT,
            progress_color=theme.ACCENT,
            command=lambda: setattr(self._voice, "auto_speak", bool(self.auto_speak.get())),
        )
        if self._voice.auto_speak:
            self.auto_speak.select()
        self.auto_speak.pack(anchor="w", padx=4, pady=(0, 8))

        # В меню показываем названия голосов, в настройках храним коды.
        self._voice_codes = {name: code for code, name in VOICES}
        names = list(self._voice_codes)
        current = next((name for code, name in VOICES if code == self._voice.voice), names[0])
        ctk.CTkLabel(parent, text="ГОЛОС  /  КЛАВИША P", font=theme.LABEL, text_color=theme.FAINT).pack(anchor="w", padx=4)
        self.voice_menu = ctk.CTkOptionMenu(
            parent,
            values=names,
            command=self.choose_voice,
            height=30,
            corner_radius=15,
            font=theme.SMALL,
            dropdown_font=theme.SMALL,
            fg_color=theme.CARD_ALT,
            button_color=theme.ACCENT,
            button_hover_color=theme.ACCENT_HOVER,
            text_color=theme.TEXT,
            dynamic_resizing=False,
        )
        self.voice_menu.set(current)
        self.voice_menu.pack(fill="x", pady=(4, 14))

    def _build_theme(self, parent, on_theme: Callable[[str], None]) -> None:
        ctk.CTkLabel(parent, text="ОФОРМЛЕНИЕ", font=theme.LABEL, text_color=theme.FAINT).pack(anchor="w", padx=4)
        self.theme_switch = ctk.CTkSegmentedButton(
            parent,
            values=[DARK, LIGHT],
            command=on_theme,
            font=theme.SMALL,
            corner_radius=15,
            fg_color=theme.CARD_ALT,
            unselected_color=theme.CARD_ALT,
            unselected_hover_color=theme.ACCENT_SOFT,
            # Выбранная часть - мягкая голубая подсветка, текст светлый в обеих частях.
            selected_color=theme.ACCENT_SOFT,
            selected_hover_color=theme.ACCENT_SOFT,
            text_color=theme.TEXT,
        )
        self.theme_switch.set(DARK if ctk.get_appearance_mode() == "Dark" else LIGHT)
        self.theme_switch.pack(fill="x", pady=(6, 0))
        ctk.CTkLabel(parent, text="CTRL+T", font=theme.LABEL, text_color=theme.FAINT).pack(anchor="e", padx=4)

    # --- действия ----------------------------------------------------------------

    def choose_voice(self, name: str) -> None:
        """Выбрать голос по названию из списка (как при выборе мышью)."""
        self.voice_menu.set(name)
        self._voice.set_voice(self._voice_codes[name])

    def show_theme(self, value: str) -> None:
        """Переключить кнопку темы без вызова on_theme (для Ctrl+T)."""
        self.theme_switch.set(value)

    def highlight(self, old_key: str | None, new_key: str) -> None:
        """Подсветить пункт открытой страницы. Перекрашиваем только два пункта."""
        for key in (old_key, new_key):
            if key is None:
                continue
            active = key == new_key
            self._buttons[key].configure(
                fg_color=theme.ACCENT_SOFT if active else "transparent",
                text_color=theme.ACCENT if active else theme.TEXT,
                font=theme.BODY_BOLD if active else theme.BODY,
            )
