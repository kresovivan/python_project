# =============================================================================
# ГЛАВНАЯ - заголовок, "Продолжить" со схемой, статистика, быстрый старт, слово дня
# =============================================================================
#
# Что это в жизни: "обложка тетради с закладкой". Сразу видно, где вы
# остановились (Enter - продолжить), сколько слов выучено, и можно
# одной клавишей начать любое упражнение.

import random

import customtkinter as ctk

from core.progress import LEARNED, LEARNING, NEW, WEAK
from core.session import CARDS, CHOICE, TYPING
from gui import theme
from gui.context import AppContext
from gui.diagram import LearningDiagram
from gui.hotkeys import KeyPress
from gui.pages.base import Page
from gui.widgets import (
    AccentButton,
    Box,
    Card,
    GhostButton,
    Muted,
    PageHeader,
    SectionLabel,
    SpeakButton,
    StatCard,
)


class HomePage(Page):
    key = "home"
    title = "Главная"
    QUICK_START = (  # клавиши 1-4 на главной открывают эти режимы
        (CARDS, "Карточки", "знакомство со словами"),
        (CHOICE, "Выбор перевода", "один из четырёх"),
        (TYPING, "Написание слова", "по памяти"),
        ("errors", "Ошибки Python", "читаем как текст"),  # не занятие, а страница чтения
    )

    def __init__(self, master, context: AppContext, number: int = 0):
        super().__init__(master, context, number)
        self.daily_word = None

        self.header = PageHeader(self, self.number, "Английский", "для программистов.", hero=True, label=self.title)
        self.header.pack(fill="x")

        self._build_hero()
        self._build_stats()
        self._build_bottom()
        self.new_daily_word()

    # --- построение ------------------------------------------------------------

    def _build_hero(self) -> None:
        """Главный блок: слева "где остановились", справа анимированная схема."""
        hero = Card(self, fg_color=theme.PANEL, height=230)
        hero.pack(fill="x", pady=(18, 0))
        hero.pack_propagate(False)  # высота блока фиксирована

        left = Box(hero, color=theme.PANEL)
        left.pack(side="left", fill="y", padx=(26, 0), pady=22)
        self.hero_label = SectionLabel(left, "", "", color=theme.ACCENT)
        self.hero_label.pack(anchor="w")
        self.hero_title = ctk.CTkLabel(left, text="", font=theme.H2, text_color=theme.TEXT, anchor="w")
        self.hero_title.pack(anchor="w", pady=(6, 0))
        self.hero_info = Muted(left, wraplength=330)
        self.hero_info.pack(anchor="w", pady=(4, 0))
        self.hero_bar = ctk.CTkProgressBar(
            left, width=300, height=4, corner_radius=2, fg_color=theme.LINE_STRONG, progress_color=theme.ACCENT
        )
        self.hero_bar.pack(anchor="w", pady=(14, 0))
        self.hero_button = AccentButton(left, "", self.continue_session, width=230)
        self.hero_button.pack(anchor="w", side="bottom")

        self.diagram = LearningDiagram(hero)
        # Отступ от края карточки - чтобы схема не залезала на скруглённые углы.
        self.diagram.pack(side="right", fill="both", expand=True, padx=(12, 3), pady=3)

    def _build_stats(self) -> None:
        row = Box(self, color=theme.BG)
        row.pack(fill="x", pady=(14, 0))
        row.columnconfigure((0, 1, 2, 3, 4), weight=1, uniform="stats")
        self.stat_cards = {
            LEARNED: StatCard(row, "выучено", theme.SUCCESS),
            LEARNING: StatCard(row, "изучаю", theme.WARNING),
            WEAK: StatCard(row, "слабые", theme.DANGER),
            NEW: StatCard(row, "впереди", theme.MUTED),
        }
        for column, card in enumerate(self.stat_cards.values()):
            card.grid(row=0, column=column, sticky="nsew", padx=(0, 12))
        self.streak_card = StatCard(row, "дней подряд", theme.ACCENT)
        self.streak_card.grid(row=0, column=4, sticky="nsew")

    def _build_bottom(self) -> None:
        bottom = Box(self, color=theme.BG)
        bottom.pack(fill="both", expand=True, pady=(14, 0))
        bottom.columnconfigure((0, 1), weight=1, uniform="bottom")
        bottom.rowconfigure(0, weight=1)

        quick = Card(bottom)
        quick.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        top = Box(quick, color=theme.CARD)
        top.pack(fill="x", padx=22, pady=(18, 8))
        SectionLabel(top, "", "быстрый старт").pack(side="left")
        self.today_label = ctk.CTkLabel(top, text="", font=theme.LABEL, text_color=theme.FAINT)
        self.today_label.pack(side="right")
        for number, (page_key, name, hint) in enumerate(self.QUICK_START, start=1):
            GhostButton(
                quick,
                f"{number}    {name}  /  {hint}",
                lambda k=page_key: self.navigator.show_page(k),
                anchor="w",
                height=36,
                corner_radius=18,
            ).pack(fill="x", padx=22, pady=3)

        self.daily = Card(bottom)
        self.daily.grid(row=0, column=1, sticky="nsew")
        SectionLabel(self.daily, "", "слово дня").pack(anchor="w", padx=22, pady=(18, 0))
        self.daily_en = ctk.CTkLabel(self.daily, text="", font=(theme.DISPLAY, 34), text_color=theme.TEXT)
        self.daily_en.pack(anchor="w", padx=22, pady=(6, 0))
        self.daily_sound = Muted(self.daily, font=theme.SOUND, text_color=theme.ACCENT)
        self.daily_sound.pack(anchor="w", padx=22)
        self.daily_ru = ctk.CTkLabel(
            self.daily, text="", font=theme.BODY, text_color=theme.TEXT, wraplength=420, anchor="w", justify="left"
        )
        self.daily_ru.pack(anchor="w", padx=22, pady=(8, 0))
        buttons = Box(self.daily, color=theme.CARD)
        buttons.pack(anchor="w", side="bottom", padx=22, pady=16)
        GhostButton(buttons, "Другое слово (Пробел)", self.new_daily_word, width=200, height=34, corner_radius=17).pack(
            side="left"
        )
        SpeakButton(buttons, lambda: self.voice.say(self.speak_text())).pack(side="left", padx=10)

    # --- жизненный цикл ------------------------------------------------------------

    def on_show(self) -> None:
        words = self.vocabulary.all_words()
        counts = self.progress.counts(words)
        total, learned = len(words), counts[LEARNED]
        percent = learned * 100 // total if total else 0
        self.header.description.configure(
            text=f"{total} слов в {len(self.vocabulary.topics())} темах. Выучено {learned} ({percent}%)."
        )
        self.header.description.pack(anchor="w", pady=(2, 0))
        for status, card in self.stat_cards.items():
            card.set(counts[status])
        self.streak_card.set(self.progress.streak())
        self.today_label.configure(text=f"СЕГОДНЯ ОТВЕТОВ: {self.progress.today_total()}")
        self._show_hero()
        self.diagram.set_words(self._diagram_words())
        self.diagram.redraw()  # цвета могли смениться вместе с темой
        self.diagram.start()

    def on_hide(self) -> None:
        self.diagram.stop()  # анимация работает только на открытой странице

    def _diagram_words(self, count: int = 12) -> list[tuple[str, str]]:
        """Слова для схемы: сначала те, что сейчас учат (слабые и начатые), потом случайные.

        Длинные фразы пропускаем - они не помещаются на плоскость схемы.
        """
        words = [w for w in self.vocabulary.all_words() if len(w.answer) <= 14]
        studying = [w for w in words if self.progress.status(w) in (WEAK, LEARNING)]
        random.shuffle(studying)
        chosen = studying[:count]
        if len(chosen) < count:
            rest = [w for w in words if w not in chosen]
            chosen += random.sample(rest, count - len(chosen))
        return [(w.answer, w.ru) for w in chosen]

    def _show_hero(self) -> None:
        session = self.settings.last_session()
        if session:
            self.hero_label.configure(text="ВЫ ОСТАНОВИЛИСЬ ЗДЕСЬ")
            self.hero_title.configure(text=self.navigator.page_title(session.mode))
            self.hero_info.configure(
                text=f"{session.topic}, слово {session.index + 1} из {session.total}.\n"
                f"Верно: {session.right}, ошибок: {session.wrong}."
            )
            self.hero_bar.set(session.fraction)
            self.hero_button.configure(text="Продолжить (Enter)")
        else:
            self.hero_label.configure(text="С ЧЕГО НАЧАТЬ")
            self.hero_title.configure(text="Первое занятие")
            self.hero_info.configure(text="Карточки по 20 слов: посмотрите слово,\nвспомните перевод, отметьте ответ.")
            self.hero_bar.set(0)
            self.hero_button.configure(text="Начать (Enter)")

    # --- действия ------------------------------------------------------------------

    def on_key(self, key: KeyPress) -> bool:
        if key.is_("Return"):
            self.continue_session()
        elif key.is_("space"):
            self.new_daily_word()
        elif key.digit and key.digit <= len(self.QUICK_START):
            self.navigator.show_page(self.QUICK_START[key.digit - 1][0])
        else:
            return False
        return True

    def continue_session(self) -> None:
        session = self.settings.last_session()
        self.navigator.show_page(session.mode if session else CARDS)

    def speak_text(self) -> str | None:
        return self.daily_word.answer if self.daily_word else None

    def new_daily_word(self) -> None:
        word = random.choice(self.vocabulary.all_words())
        self.daily_word = word
        self.voice.prefetch(word.answer)
        self.daily_en.configure(text=word.en)
        self.daily_sound.configure(text=f"[ {word.sound} ]")
        self.daily_ru.configure(text=f"{word.ru}\n{word.topic}")
