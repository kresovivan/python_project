# =============================================================================
# ОБ АВТОРЕ - кто и как создал программу
# =============================================================================
#
# Что это в жизни: "последняя страница книги", где рассказано об авторе.
# Здесь две карточки (автор и соавтор), несколько цифр о проекте и кнопка,
# которая открывает исходный код на GitHub.
#
# Тексты - данные, поэтому они вынесены в константы в начале файла:
# поменять рассказ можно, не трогая код страницы.
# Цифры о проекте (слов, тем, ошибок) берутся из словаря и списка ошибок,
# а не вписаны руками: добавят слово - число на странице обновится само.

import webbrowser

import customtkinter as ctk

from gui import theme
from gui.context import AppContext
from gui.pages.base import Page
from gui.widgets import AccentButton, Box, Card, Muted, SectionLabel, StatCard

PROJECT_URL = "https://github.com/kresovivan/python_project"

AUTHOR_NAME = "Kresov Ivan"
AUTHOR_NAME_RU = "Иван Кресов"
AUTHOR_ROLE = "автор идеи и создатель"
AUTHOR_TEXT = (
    "Изучает Python по книгам, на практике и в собственных проектах: "
    "автоматизация рутинных задач, ООП, работа с базами данных.\n\n"
    "Тренажёр вырос из личной задачи - свободно читать документацию и сообщения "
    "об ошибках по-английски. Иван придумал программу, решил, чему и как она "
    "учит, выбрал оформление и проверял каждую версию на себе."
)

COAUTHOR_NAME = "Claude Code"
COAUTHOR_ROLE = "соавтор, ИИ-помощник программиста от Anthropic"
COAUTHOR_TEXT = (
    "Напарник по программированию: превращал замысел автора в код по правилам "
    "ООП, покрывал его тестами по методике TDD, находил и исправлял ошибки, "
    "писал документацию и подробные комментарии на русском, чтобы код читался "
    "как учебник.\n\n"
    "Каждое решение объяснялось простым языком, а последнее слово всегда "
    "оставалось за автором."
)

FOOTER = "English for Programmers. Создано Kresov Ivan совместно с Claude Code, 2026."


class AboutPage(Page):
    key = "about"
    title = "Об авторе"
    tagline = "Кто сделал программу."
    description = "Тренажёр придуман и написан вдвоём: человеком и искусственным интеллектом."

    PAD = 24  # отступ текста от краёв карточки (до масштабирования)

    def __init__(self, master, context: AppContext, number: int = 0):
        super().__init__(master, context, number)
        self.build_header()

        people = Box(self, color=theme.BG)
        people.pack(fill="x", pady=(14, 0))
        # uniform - обе колонки одной ширины, как бы ни отличалась длина текста.
        people.columnconfigure((0, 1), weight=1, uniform="people")
        self._person_card(people, "автор", AUTHOR_NAME, AUTHOR_NAME_RU, AUTHOR_ROLE, AUTHOR_TEXT).grid(
            row=0, column=0, sticky="nsew", padx=(0, 8)
        )
        self._person_card(people, "соавтор", COAUTHOR_NAME, "", COAUTHOR_ROLE, COAUTHOR_TEXT).grid(
            row=0, column=1, sticky="nsew", padx=(8, 0)
        )

        self._build_numbers()
        self._build_footer()

    # --- построение ------------------------------------------------------------

    def _person_card(self, parent, label: str, name: str, name_ru: str, role: str, text: str) -> Card:
        """Карточка человека (или ИИ): метка, имя, роль, рассказ."""
        pad = self.PAD
        card = Card(parent)
        SectionLabel(card, "", label, color=theme.ACCENT).pack(anchor="w", padx=pad, pady=(18, 0))
        title = Box(card, color=theme.CARD)
        title.pack(anchor="w", padx=pad, pady=(4, 0))
        ctk.CTkLabel(title, text=name, font=(theme.DISPLAY, 30), text_color=theme.TEXT).pack(side="left")
        if name_ru:
            Muted(title, name_ru, font=theme.H3, text_color=theme.ACCENT).pack(side="left", padx=(14, 0), pady=(8, 0))
        Muted(card, role.upper(), font=theme.LABEL, text_color=theme.FAINT).pack(anchor="w", padx=pad, pady=(4, 10))
        story = Muted(card, text)
        story.pack(anchor="w", padx=pad, pady=(0, 20))
        # Ширина абзаца подстраивается под карточку: окно можно растянуть или сузить.
        # event.width - в пикселях экрана, а wraplength у CTkLabel задаётся в логических
        # единицах (CustomTkinter сам умножает его на масштаб), поэтому делим на масштаб.
        card.bind("<Configure>", lambda event: self._fit_text(story, event.width))
        return card

    def _fit_text(self, label: Muted, card_width: int) -> None:
        scale = ctk.ScalingTracker.get_widget_scaling(self)
        label.configure(wraplength=max(200, card_width / scale - 2 * self.PAD - 8))

    def _build_numbers(self) -> None:
        """Плитки с цифрами о проекте: сколько всего в программе."""
        SectionLabel(self, "", "что получилось").pack(anchor="w", pady=(14, 6))
        row = Box(self, color=theme.BG)
        row.pack(fill="x")
        numbers = (
            ("слов в словаре", len(self.vocabulary), theme.ACCENT),
            ("тем", len(self.vocabulary.topics()), theme.SUCCESS),
            ("ошибок Python с разбором", len(self.context.errors), theme.WARNING),
        )
        row.columnconfigure(tuple(range(len(numbers))), weight=1, uniform="numbers")
        for column, (caption, value, color) in enumerate(numbers):
            card = StatCard(row, caption, color)
            card.set(value)
            card.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 8, 0))

    def _build_footer(self) -> None:
        footer = Box(self, color=theme.BG)
        footer.pack(fill="x", pady=(14, 0))
        AccentButton(footer, "Исходный код на GitHub", self.open_project, width=250).pack(side="left")
        signature = Box(footer, color=theme.BG)
        signature.pack(side="left", padx=18)
        Muted(signature, FOOTER, font=theme.SMALL, text_color=theme.MUTED).pack(anchor="w")
        Muted(signature, PROJECT_URL, font=theme.LABEL, text_color=theme.FAINT).pack(anchor="w")

    # --- действия ------------------------------------------------------------------

    def open_project(self) -> None:
        """Открыть страницу проекта на GitHub в браузере по умолчанию."""
        webbrowser.open(PROJECT_URL)

    def speak_text(self) -> str | None:
        # По клавише P программа представляется по-английски.
        return "English for Programmers. Created by Ivan Kresov together with Claude Code."
