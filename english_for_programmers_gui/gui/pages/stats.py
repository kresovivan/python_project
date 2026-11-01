# =============================================================================
# ПРОГРЕСС - общая полоска, график активности за 2 недели, прогресс по темам
# =============================================================================

import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

from core.progress import LEARNED, LEARNING, NEW, WEAK
from gui import theme
from gui.context import AppContext
from gui.pages.base import Page
from gui.widgets import Box, Card, GhostButton, Muted, SectionLabel, StatCard


class TopicBars(Card):
    """Список тем с полосками прогресса, нарисованный на одном холсте.

    Раньше каждая строка была тремя виджетами CustomTkinter (18 тем = 54
    виджета), и все они перерисовывались при каждом изменении размера окна.
    Один tk.Canvas рисует те же строки за миллисекунды.
    """

    ROW = 40  # высота строки до масштабирования
    NAME_WIDTH = 340  # ширина колонки с названием темы
    COUNT_WIDTH = 110  # ширина колонки "12 / 293"

    def __init__(self, master):
        super().__init__(master)
        self.rows: list[tuple[str, int, int]] = []
        self.canvas = tk.Canvas(self, highlightthickness=0, bd=0)
        self.scrollbar = ctk.CTkScrollbar(self, command=self.canvas.yview, button_color=theme.BORDER)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y", padx=(0, 6), pady=12)
        self.canvas.pack(side="left", fill="both", expand=True, padx=(18, 4), pady=12)
        self.canvas.bind("<Configure>", lambda event: self.draw())
        # Прокрутка колёсиком мыши: delta=120 - один "щелчок" колёсика.
        self.canvas.bind("<MouseWheel>", lambda event: self.canvas.yview_scroll(-event.delta // 120, "units"))

    def set(self, rows: list[tuple[str, int, int]]) -> None:
        """rows - список (название темы, выучено, всего)."""
        self.rows = rows
        self.draw()

    def draw(self) -> None:
        canvas = self.canvas
        canvas.delete("all")
        canvas.configure(bg=theme.pick(theme.CARD))
        s = self._get_widget_scaling()  # масштаб экрана: 1.0, 1.25, 2.0 ...
        width = canvas.winfo_width()
        if width < 50:
            return
        row, bar_start = self.ROW * s, self.NAME_WIDTH * s
        bar_end = width - self.COUNT_WIDTH * s
        font = (theme.FONT, -round(14 * s))
        small = (theme.MONO, -round(11 * s))
        for i, (title, done, total) in enumerate(self.rows):
            y = i * row + row / 2
            canvas.create_text(0, y, text=title, anchor="w", font=font, fill=theme.pick(theme.TEXT))
            # Полоска - толстая линия со скруглёнными концами (capstyle="round").
            thickness = 10 * s
            canvas.create_line(bar_start, y, bar_end, y, width=thickness, capstyle="round", fill=theme.pick(theme.BORDER))
            if done:
                filled = bar_start + (bar_end - bar_start) * done / total
                canvas.create_line(
                    bar_start, y, max(filled, bar_start + 1), y, width=thickness, capstyle="round",
                    fill=theme.pick(theme.SUCCESS),
                )
            canvas.create_text(width - 4 * s, y, text=f"{done} / {total}", anchor="e", font=small, fill=theme.pick(theme.MUTED))
        canvas.configure(scrollregion=(0, 0, width, len(self.rows) * row))


class StatsPage(Page):
    key = "stats"
    title = "Прогресс"
    tagline = "Шаг за шагом."

    def __init__(self, master, context: AppContext):
        super().__init__(master, context)

        header = self.build_header()
        GhostButton(
            header, "Сбросить прогресс", self.reset, width=180, height=34, corner_radius=17,
            text_color=theme.DANGER, border_color=theme.DANGER,
        ).place(relx=1.0, rely=0.5, anchor="e")

        # --- общая полоска ----------------------------------------------------
        total_card = Card(self)
        total_card.pack(fill="x", pady=(18, 0))
        SectionLabel(total_card, "", "всего выучено").pack(anchor="w", padx=24, pady=(16, 0))
        self.total_label = ctk.CTkLabel(total_card, text="", font=theme.H2, text_color=theme.TEXT)
        self.total_label.pack(anchor="w", padx=24, pady=(2, 10))
        self.total_bar = ctk.CTkProgressBar(
            total_card, height=6, corner_radius=3, fg_color=theme.BORDER, progress_color=theme.SUCCESS
        )
        self.total_bar.pack(fill="x", padx=24, pady=(0, 20))

        # --- числа по статусам + график -----------------------------------------
        middle = Box(self, color=theme.BG)
        middle.pack(fill="x", pady=(14, 0))
        middle.columnconfigure((0, 1), weight=1, uniform="m")

        cards = Box(middle, color=theme.BG)
        cards.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        cards.columnconfigure((0, 1), weight=1, uniform="c")
        self.stat_cards = {
            LEARNED: StatCard(cards, "выучено", theme.SUCCESS),
            LEARNING: StatCard(cards, "изучаю", theme.WARNING),
            WEAK: StatCard(cards, "слабые", theme.DANGER),
            NEW: StatCard(cards, "новые", theme.MUTED),
        }
        for i, card in enumerate(self.stat_cards.values()):
            card.grid(row=i // 2, column=i % 2, sticky="nsew", padx=(0, 8) if i % 2 == 0 else 0, pady=(0, 8))

        chart_card = Card(middle)
        chart_card.grid(row=0, column=1, sticky="nsew")
        SectionLabel(chart_card, "", "ответы за 14 дней").pack(anchor="w", padx=20, pady=(14, 0))
        Muted(chart_card, "мятным - верные, красным - ошибки", font=theme.SMALL).pack(anchor="w", padx=20)
        # Обычный tkinter.Canvas - "холст", на котором рисуем прямоугольники сами.
        # Высоту умножаем на масштаб экрана: tk.Canvas сам этого не делает.
        scale = ctk.ScalingTracker.get_widget_scaling(chart_card)
        self.chart = tk.Canvas(chart_card, height=round(170 * scale), highlightthickness=0, bd=0)
        self.chart.pack(fill="both", expand=True, padx=16, pady=(6, 14))
        # Перерисовываем график, когда меняется размер окна.
        self.chart.bind("<Configure>", lambda event: self.draw_chart())

        # --- темы ---------------------------------------------------------------
        SectionLabel(self, "", "по темам").pack(anchor="w", pady=(16, 6))
        self.topic_bars = TopicBars(self)
        self.topic_bars.pack(fill="both", expand=True)

    def on_show(self) -> None:
        words = self.vocabulary.all_words()
        counts = self.progress.counts(words)
        learned, total = counts[LEARNED], len(words)
        percent = learned * 100 / total if total else 0
        self.total_label.configure(text=f"Выучено {learned} из {total} слов, {percent:.1f}%")
        self.total_bar.set(learned / total if total else 0)
        for status, card in self.stat_cards.items():
            card.set(counts[status])
        rows = []
        for topic in self.vocabulary.topics():
            topic_words = self.vocabulary.words(topic)
            rows.append((topic, self.progress.counts(topic_words)[LEARNED], len(topic_words)))
        self.topic_bars.set(rows)
        self.draw_chart()

    def draw_chart(self) -> None:
        canvas = self.chart
        canvas.delete("all")
        canvas.configure(bg=theme.pick(theme.CARD))
        width, height = canvas.winfo_width(), canvas.winfo_height()
        if width < 50:
            return  # окно ещё не нарисовано

        # tk.Canvas не масштабируется сам (см. CLAUDE.md), поэтому все отступы
        # и шрифт умножаем на масштаб экрана s. Раньше отступы были заданы
        # для масштаба 100%, и при 200% даты под графиком обрезались снизу.
        s = ctk.ScalingTracker.get_widget_scaling(canvas)
        # Минус перед размером шрифта - размер в пикселях, а не в пунктах.
        # Так мы точно знаем высоту текста и можем оставить под него место.
        font = (theme.MONO, -round(11 * s))
        top_space = 22 * s  # место над самым высоким столбиком для его числа
        bottom = height - 22 * s  # нижний край столбиков, ниже - подписи дат

        history = self.progress.history(14)
        top = max((right + wrong for _, right, wrong in history), default=0) or 1
        slot = width / len(history)
        bar_width = slot * 0.6
        scale = (bottom - top_space) / top

        for i, (day, right, wrong) in enumerate(history):
            x0 = i * slot + (slot - bar_width) / 2
            x1 = x0 + bar_width
            green_top = bottom - right * scale
            # Тонкая "дорожка" под каждым днём - видно все 14 дней, даже пустые.
            canvas.create_rectangle(x0, top_space, x1, bottom, fill=theme.pick(theme.CARD_ALT), width=0)
            red_top = green_top - wrong * scale
            if right:
                canvas.create_rectangle(x0, green_top, x1, bottom, fill=theme.pick(theme.SUCCESS), width=0)
            if wrong:
                canvas.create_rectangle(x0, red_top, x1, green_top, fill=theme.pick(theme.DANGER), width=0)
            # anchor="s" (south, юг) - точка (x, y) задаёт НИЖНИЙ край текста,
            # а не его середину. Так текст никогда не залезет ниже этой точки.
            if right + wrong:
                canvas.create_text(
                    (x0 + x1) / 2, red_top - 3 * s, text=str(right + wrong), anchor="s",
                    fill=theme.pick(theme.MUTED), font=font,
                )
            canvas.create_text(
                (x0 + x1) / 2, height - 2 * s, text=day.strftime("%d"), anchor="s",
                fill=theme.pick(theme.FAINT), font=font,
            )

    def reset(self) -> None:
        if messagebox.askyesno("Сбросить прогресс", "Удалить весь прогресс изучения? Это нельзя отменить."):
            self.progress.reset()
            self.on_show()
