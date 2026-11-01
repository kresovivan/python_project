# =============================================================================
# ЧИТАЕМ ОШИБКИ PYTHON - настоящие сообщения об ошибках с разбором
# =============================================================================
#
# Что это в жизни: "листаем сборник ошибок". Одна карточка на экране,
# пробел - открыть перевод и разбор, стрелки - листать. Карточки - список
# ERRORS (core/errors_data.py), место в сборнике запоминается в Settings.

import customtkinter as ctk

from gui import theme
from gui.context import AppContext
from gui.hotkeys import KeyPress
from gui.pages.base import Page
from gui.widgets import AccentButton, Box, Card, GhostButton, Muted, SpeakButton


class ErrorsPage(Page):
    key = "errors"
    title = "Ошибки Python"
    tagline = "Читаем как текст."
    description = "Прочитайте ошибку и попробуйте понять её сами. Потом откройте перевод."

    def __init__(self, master, context: AppContext, number: int = 0):
        super().__init__(master, context, number)
        self.errors = context.errors
        # Номер ошибки запоминается между запусками.
        self.index = self.settings.get("errors_index", 0) % len(self.errors)
        self.revealed = False

        self.build_header()

        card = Card(self)
        card.pack(fill="both", expand=True, pady=(18, 0))

        top = Box(card, color=theme.CARD)
        top.pack(fill="x", padx=30, pady=(24, 10))
        self.counter = Muted(top, font=theme.LABEL, text_color=theme.FAINT)
        self.counter.pack(side="left")
        SpeakButton(top, lambda: self.voice.say(self.speak_text()), text="Прочитать вслух (P)").pack(side="right")

        # "Терминал" с текстом ошибки
        terminal = ctk.CTkFrame(card, fg_color=theme.TERMINAL_BG, corner_radius=14, border_width=1, border_color=theme.LINE_STRONG)
        terminal.pack(fill="x", padx=30)
        ctk.CTkLabel(terminal, text="Traceback (most recent call last):  ...", font=theme.CODE, text_color=theme.TERMINAL_DIM).pack(
            anchor="w", padx=20, pady=(16, 0)
        )
        self.message = ctk.CTkLabel(
            terminal, text="", font=theme.CODE_BIG, text_color=theme.TERMINAL_TEXT, wraplength=820, justify="left"
        )
        self.message.pack(anchor="w", padx=20, pady=(4, 18))

        self.reveal_button = AccentButton(card, "Показать перевод    Пробел / Enter", self.reveal, width=320)

        self.details = Box(card, color=theme.CARD)
        self.rows = {}
        for key, caption in (("ru", "Перевод"), ("words", "Слова"), ("hint", "Что делать")):
            Muted(self.details, caption.upper(), font=theme.LABEL, text_color=theme.FAINT).pack(anchor="w", pady=(14, 2))
            label = ctk.CTkLabel(
                self.details, text="", font=theme.H3 if key == "ru" else theme.BODY, text_color=theme.TEXT,
                wraplength=820, justify="left", anchor="w",
            )
            label.pack(anchor="w")
            self.rows[key] = label

        nav = Box(card, color=theme.CARD)
        nav.pack(side="bottom", fill="x", padx=30, pady=24)
        GhostButton(nav, "Назад", self.prev, width=160).pack(side="left")
        GhostButton(nav, "Дальше", self.next, width=160).pack(side="right")
        Muted(nav, "СТРЕЛКИ ВЛЕВО И ВПРАВО", font=theme.LABEL, text_color=theme.FAINT, anchor="center").pack(side="left", expand=True)

    def on_show(self) -> None:
        self.render()

    def render(self) -> None:
        error = self.errors[self.index]
        self.revealed = False
        self.counter.configure(text=f"ОШИБКА {self.index + 1:02d} ИЗ {len(self.errors)}")
        self.message.configure(text=error.message)
        self.details.pack_forget()
        self.reveal_button.pack(anchor="w", padx=30, pady=24)
        self.settings.set("errors_index", self.index)

    def reveal(self) -> None:
        if self.revealed:
            return
        self.revealed = True
        error = self.errors[self.index]
        self.rows["ru"].configure(text=error.ru)
        self.rows["words"].configure(text=error.words)
        self.rows["hint"].configure(text=error.hint)
        self.reveal_button.pack_forget()
        self.details.pack(fill="x", padx=30, pady=(6, 0))

    def next(self) -> None:
        self.index = (self.index + 1) % len(self.errors)  # % - по кругу: после последней снова первая
        self.render()

    def prev(self) -> None:
        self.index = (self.index - 1) % len(self.errors)
        self.render()

    def speak_text(self) -> str | None:
        return self.errors[self.index].message

    def on_key(self, key: KeyPress) -> bool:
        if key.is_("space", "Return"):
            self.reveal()
        elif key.is_("Right"):
            self.next()
        elif key.is_("Left"):
            self.prev()
        else:
            return False
        return True
