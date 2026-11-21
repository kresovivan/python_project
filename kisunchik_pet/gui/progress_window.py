# -*- coding: utf-8 -*-
"""Окно прогресса обучения: графики и управление.

Что это в жизни: "табло с медальками". Сверху - активность по дням
недели (сколько слов показали и произнесли), ниже - все блоки слов
с полосками "пройдено/всего" и кнопкой начать блок заново. Всё в
цветах Кисунчика: сливки, карамель, рыжий.

Важно: экран пользователя может быть с масштабом 150-200%, поэтому
все отступы и высоты строк считаются от РЕАЛЬНЫХ размеров шрифта
(tkfont.metrics), а не зашиты числами - иначе строки налипают друг
на друга. Список блоков собран из обычных виджетов: tkinter сам
разложит их без наложений при любом масштабе.
"""

import tkinter as tk
from tkinter import font as tkfont
from tkinter import messagebox

# Палитра Кисунчика.
BG = "#FFF9F1"
TEXT = "#4A3226"
SUBTLE = "#8A7364"
TRACK = "#F3E3D3"
FILL = "#F0913C"
FILL_DARK = "#C85F14"
ACCENT = "#E87E2B"

GROUP_TITLES = {"basics": "Азбука и основы", "topics": "Темы",
                "speech": "Части речи", "style": "Фразы и стиль"}
GROUP_ORDER = ["basics", "topics", "speech", "style"]
WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


class ProgressWindow:
    """Табло прогресса. Один экземпляр на приложение."""

    def __init__(self, root: tk.Tk, tutor, progress):
        self._tutor = tutor
        self._progress = progress
        self.win = tk.Toplevel(root)
        self.win.title("Кисунчик - прогресс обучения")
        self.win.configure(bg=BG)
        self.win.attributes("-topmost", True)
        self.win.protocol("WM_DELETE_WINDOW", self.close)
        # Шрифты как объекты: от них меряем строки и колонки.
        self.f_text = tkfont.Font(family="Segoe UI", size=10)
        self.f_bold = tkfont.Font(family="Segoe UI", size=10, weight="bold")
        self.f_header = tkfont.Font(family="Segoe UI", size=13, weight="bold")
        self._build()
        self.refresh()

    # --- каркас окна ---

    def _build(self) -> None:
        tk.Label(self.win, text="Прогресс обучения", bg=BG, fg=TEXT,
                 font=self.f_header).pack(pady=(12, 2), anchor="w", padx=16)

        # График по дням недели (канва, но отступы - от метрик шрифта).
        self.week_canvas = tk.Canvas(self.win, bg=BG, highlightthickness=0)
        self.week_canvas.pack(padx=16, pady=(0, 6), fill="x")

        tk.Label(self.win, text="Блоки слов", bg=BG, fg=TEXT,
                 font=self.f_bold).pack(anchor="w", padx=16)

        # Прокручиваемый список блоков из обычных виджетов.
        frame = tk.Frame(self.win, bg=BG)
        frame.pack(fill="both", expand=True, padx=16, pady=(0, 6))
        self.list_canvas = tk.Canvas(frame, bg=BG, highlightthickness=0,
                                     height=320)
        scroll = tk.Scrollbar(frame, orient="vertical",
                              command=self.list_canvas.yview)
        self.list_canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.list_canvas.pack(side="left", fill="both", expand=True)
        self.rows = tk.Frame(self.list_canvas, bg=BG)
        self._rows_id = self.list_canvas.create_window(
            (0, 0), window=self.rows, anchor="nw")
        self.rows.bind("<Configure>", self._on_rows_configure)
        self.list_canvas.bind("<Configure>", self._on_list_resize)
        self.list_canvas.bind_all("<MouseWheel>", self._on_wheel)

        # Кнопки внизу.
        bar = tk.Frame(self.win, bg=BG)
        bar.pack(fill="x", padx=16, pady=(4, 12))
        self._button(bar, "Обновить", self.refresh).pack(side="left")
        self._button(bar, "Сбросить всё", self._reset_all).pack(side="left",
                                                                padx=8)
        self._button(bar, "Закрыть", self.close).pack(side="right")

    def _button(self, parent, text, command) -> tk.Button:
        """Карамельная кнопка."""
        return tk.Button(parent, text=text, command=command,
                         font=self.f_text, bg=ACCENT, fg="#FFFFFF",
                         activebackground=FILL_DARK,
                         activeforeground="#FFFFFF", relief="flat",
                         padx=12, pady=4, cursor="hand2")

    def _on_rows_configure(self, _event) -> None:
        self.list_canvas.configure(scrollregion=self.list_canvas.bbox("all"))

    def _on_list_resize(self, event) -> None:
        # Растягиваем вложенный фрейм на всю ширину канвы.
        self.list_canvas.itemconfigure(self._rows_id, width=event.width)

    def _on_wheel(self, event) -> None:
        if self.win.winfo_exists():
            self.list_canvas.yview_scroll(int(-event.delta / 120), "units")

    # --- отрисовка ---

    def refresh(self) -> None:
        """Перерисовать оба графика свежими данными."""
        self._draw_week()
        self._draw_categories()

    def _draw_week(self) -> None:
        """Столбики активности по дням недели."""
        c = self.week_canvas
        c.delete("all")
        shown, said = self._progress.weekday_totals()
        peak = max(shown + [1])
        lh = self.f_text.metrics("linespace")
        blh = self.f_bold.metrics("linespace")

        c.create_text(0, 4, anchor="nw", text="Слова по дням недели",
                      fill=TEXT, font=self.f_bold)
        legend_y = 4 + blh + 6
        c.create_rectangle(0, legend_y + 3, 12, legend_y + 15, fill=FILL,
                           outline="")
        c.create_text(18, legend_y + lh // 2 + 3, anchor="w",
                      text="показано", fill=SUBTLE, font=self.f_text)
        x2 = 18 + self.f_text.measure("показано") + 24
        c.create_rectangle(x2, legend_y + 3, x2 + 12, legend_y + 15,
                           fill=FILL_DARK, outline="")
        c.create_text(x2 + 18, legend_y + lh // 2 + 3, anchor="w",
                      text="произнесено", fill=SUBTLE, font=self.f_text)

        top = legend_y + lh + 14
        bottom = top + 90
        width = max(c.winfo_width(), 520)
        slot = width / 7
        for i, name in enumerate(WEEKDAYS):
            x0 = i * slot + 12
            x1 = x0 + slot - 24
            h = int((bottom - top) * shown[i] / peak)
            c.create_rectangle(x0, bottom - h, x1, bottom, fill=FILL,
                               outline="")
            h2 = int((bottom - top) * min(said[i], shown[i]) / peak)
            c.create_rectangle(x0 + 6, bottom - h2, x1 - 6, bottom,
                               fill=FILL_DARK, outline="")
            c.create_text((x0 + x1) / 2, bottom - h - 6, anchor="s",
                          text=str(shown[i]), fill=TEXT, font=self.f_text)
            c.create_text((x0 + x1) / 2, bottom + 4, anchor="n", text=name,
                          fill=SUBTLE, font=self.f_text)
        c.configure(height=bottom + 4 + lh + 8)

    def _draw_categories(self) -> None:
        """Полоски прогресса по всем блокам (виджеты, без наложений)."""
        for child in self.rows.winfo_children():
            child.destroy()
        groups = self._tutor.category_groups()
        row = 0
        for group_key in GROUP_ORDER:
            cats = groups.get(group_key)
            if not cats:
                continue
            tk.Label(self.rows, text=GROUP_TITLES.get(group_key, group_key),
                     bg=BG, fg=SUBTLE, font=self.f_bold, anchor="w"
                     ).grid(row=row, column=0, columnspan=4, sticky="w",
                            pady=(10, 2))
            row += 1
            for cat in cats:
                done, total = self._tutor.category_status(cat["id"])
                ratio = done / total if total else 0
                tk.Label(self.rows, text=cat["title"], bg=BG, fg=TEXT,
                         font=self.f_text, anchor="w"
                         ).grid(row=row, column=0, sticky="w", padx=(12, 8))
                bar = tk.Canvas(self.rows, width=170, height=14, bg=BG,
                                highlightthickness=0)
                bar.create_rectangle(0, 0, 170, 14, fill=TRACK, outline="")
                if ratio > 0:
                    bar.create_rectangle(0, 0, max(4, int(170 * ratio)), 14,
                                         fill=FILL, outline="")
                bar.grid(row=row, column=1, sticky="w", pady=3)
                tk.Label(self.rows, text=f"{done}/{total} ({ratio:.0%})",
                         bg=BG, fg=TEXT, font=self.f_text, anchor="w",
                         width=16).grid(row=row, column=2, sticky="w",
                                        padx=(8, 4))
                again = tk.Label(self.rows, text="заново", bg=BG, fg=ACCENT,
                                 font=self.f_text, cursor="hand2")
                again.grid(row=row, column=3, sticky="e", padx=(4, 0))
                again.bind("<Button-1>",
                           lambda _e, cid=cat["id"]: self._reset_category(cid))
                row += 1
        self.rows.columnconfigure(0, minsize=self.f_text.measure("М" * 34))
        self.rows.columnconfigure(3, weight=1)

    # --- управление ---

    def _reset_category(self, category_id: str) -> None:
        title = self._tutor.category_title(category_id)
        if messagebox.askyesno(
                "Кисунчик", f"Начать блок \"{title}\" заново?\n"
                f"Закладка вернётся к первому слову.",
                parent=self.win):
            self._progress.reset_category(category_id)
            self._progress.save(force=True)
            self.refresh()

    def _reset_all(self) -> None:
        if messagebox.askyesno(
                "Кисунчик", "Сбросить ВЕСЬ прогресс обучения?\n"
                "Закладки всех блоков и счётчики слов обнулятся.",
                parent=self.win):
            self._progress.reset_all()
            self._progress.save(force=True)
            self.refresh()

    def close(self) -> None:
        if self.win.winfo_exists():
            self.win.destroy()

    def is_alive(self) -> bool:
        return bool(self.win.winfo_exists())
