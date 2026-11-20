# =============================================================================
# ГРАММАТИКА - правила в табличках для тех, кто начинает с нуля
# =============================================================================
#
# Что это в жизни: "тетрадь с правилами". Слева оглавление: темы сгруппированы
# по разделам (Основы, Времена, ...), список прокручивается. Справа выбранная
# тема: объяснение простыми словами, таблицы и совет.
# Слова языка в таблицах голубые: щёлкните по такому - оно прозвучит.
#
# Как переключать темы: щелчком в списке или стрелками вверх и вниз.
# Данные (темы, таблицы) - у языка (core/language.py): английская грамматика
# в core/grammar.py, китайская - в core/grammar_zh.py. Страница только рисует.
#
# Наследник SoundsPage - та же страница с другой тетрадью: китайские
# "Звуки и тоны" (core/pinyin.py). Отличаются они только тем, ЧТО показывать
# (метод book), поэтому весь остальной код общий.
#
# Почему таблицы из tk.Label, а не из CTkLabel: каждая метка CustomTkinter -
# это отдельный холст, а в теме бывает 40-60 клеток. Обычные метки tkinter
# создаются мгновенно. Их цвета и размер шрифта задаём сами (theme.pick и
# масштаб экрана), поэтому при смене темы оформления тема перерисовывается.

import tkinter as tk

import customtkinter as ctk

from core.grammar import GrammarTopic, Table
from gui import theme
from gui.context import AppContext
from gui.hotkeys import KeyPress
from gui.pages.base import Page
from gui.widgets import Box, Card, Muted, SectionLabel

CELL_WIDTH = 250  # самая широкая клетка, дальше текст переносится (до масштабирования)
CELL_PADDING = 12  # отступ текста от края клетки слева и справа


class GrammarPage(Page):
    key = "grammar"
    title = "Грамматика"
    tagline = "Правила в табличках."
    index_setting = "grammar_index"  # где в настройках запомнить открытую тему

    def __init__(self, master, context: AppContext, number: int = 0):
        super().__init__(master, context, number)
        self.topics = self.book()
        # Описание зависит от языка, поэтому задаём его у объекта, а не у класса.
        self.description = (
            f"{len(self.topics)} тем по разделам, от простого к сложному. "
            "Щёлкните по голубому слову - оно прозвучит."
        )
        self.index = self.settings.get(self.index_setting, 0) % len(self.topics)
        self.cells: list[tk.Label] = []  # клетки таблиц текущей темы (нужны и тестам)
        self._cell_columns: list[int] = []  # сколько колонок в таблице каждой клетки

        self.build_header()
        body = Box(self, color=theme.BG)
        body.pack(fill="both", expand=True, pady=(16, 0))
        self._build_topic_list(body)
        self._build_content(body)

    # --- построение ------------------------------------------------------------

    def _build_topic_list(self, parent) -> None:
        """Оглавление: разделы с подписями, под ними по кнопке на тему.

        Тем около 50, на экран они не помещаются, поэтому список прокручивается
        (CTkScrollableFrame - рамка с полосой прокрутки).
        """
        column = Box(parent, color=theme.BG, width=290)
        column.pack(side="left", fill="y")
        column.pack_propagate(False)  # ширина не зависит от длины названий
        # Подсказку кладём первой с side="bottom": так она всегда видна внизу,
        # а список занимает всё остальное место над ней.
        Muted(column, "СТРЕЛКИ ВВЕРХ И ВНИЗ", font=theme.LABEL, text_color=theme.FAINT).pack(
            side="bottom", anchor="w", pady=(8, 0)
        )
        self.topic_list = ctk.CTkScrollableFrame(
            column, fg_color=theme.BG, scrollbar_button_color=theme.BORDER, corner_radius=0
        )
        self.topic_list.pack(fill="both", expand=True)
        self.topic_buttons: list[ctk.CTkButton] = []
        self.section_labels: list[ctk.CTkLabel] = []
        for index, topic in enumerate(self.topics):
            if index == 0 or topic.section != self.topics[index - 1].section:
                # Первая тема нового раздела: сначала подпись раздела.
                label = SectionLabel(self.topic_list, "", topic.section)
                label.pack(anchor="w", pady=(0 if index == 0 else 12, 4))
                self.section_labels.append(label)
            button = ctk.CTkButton(
                self.topic_list,
                text=f"{index + 1:02d}   {topic.title}",
                anchor="w",
                height=34,
                corner_radius=10,
                font=theme.SMALL,
                fg_color="transparent",
                hover_color=theme.ACCENT_SOFT,
                text_color=theme.TEXT,
                command=lambda i=index: self.show(i),
            )
            button.pack(fill="x", pady=1, padx=(0, 6))
            self.topic_buttons.append(button)

    def _build_content(self, parent) -> None:
        """Справа: название темы и объяснение, ниже - прокручиваемые таблицы."""
        card = Card(parent)
        card.pack(side="left", fill="both", expand=True, padx=(16, 0))
        # Где мы: "ВРЕМЕНА / ТЕМА 22 ИЗ 50".
        self.topic_place = ctk.CTkLabel(card, text="", font=theme.LABEL, text_color=theme.FAINT, anchor="w")
        self.topic_place.pack(anchor="w", padx=26, pady=(16, 0))
        self.topic_title = ctk.CTkLabel(card, text="", font=theme.H2, text_color=theme.TEXT, anchor="w")
        self.topic_title.pack(anchor="w", padx=26, pady=(2, 0))
        self.intro = Muted(card)
        self.intro.pack(anchor="w", padx=26, pady=(4, 8))
        self.tip: Muted | None = None  # совет под таблицами текущей темы
        self._text_width = 600  # ширина абзаца в логических единицах, уточняется ниже
        # Ширина абзацев подстраивается под карточку. event.width - пиксели экрана,
        # а wraplength у CTkLabel - логические единицы, поэтому делим на масштаб.
        card.bind("<Configure>", self._fit_text)
        # CTkScrollableFrame - рамка с полосой прокрутки: таблицы бывают длинными.
        self.scroll = ctk.CTkScrollableFrame(
            card, fg_color=theme.CARD, scrollbar_button_color=theme.BORDER, corner_radius=0
        )
        self.scroll.pack(fill="both", expand=True, padx=(20, 8), pady=(0, 14))

    def _fit_text(self, event) -> None:
        scale = ctk.ScalingTracker.get_widget_scaling(self)
        self._text_width = max(300, event.width / scale - 70)
        self.intro.configure(wraplength=self._text_width)
        if self.tip is not None:
            self.tip.configure(wraplength=self._text_width - 30)
        # Карточка стала шире или уже - клетки таблиц тоже переносят текст по-новому.
        for cell, columns in zip(self.cells, self._cell_columns):
            cell.configure(wraplength=self._cell_wrap(columns))

    def _cell_wrap(self, columns: int) -> int:
        """Ширина строки в клетке (в пикселях экрана), после которой текст переносится.

        Вся ширина карточки делится поровну между колонками. Так таблица из
        4 колонок с длинным текстом не уходит за правый край, а переносит
        текст на следующую строку. Слишком узкой (меньше 90) клетку не делаем.
        """
        scale = ctk.ScalingTracker.get_widget_scaling(self)
        share = self._text_width / columns - 2 * CELL_PADDING - 2  # 2 - линии сетки
        return round(max(90, min(CELL_WIDTH, share)) * scale)

    # --- показ темы ------------------------------------------------------------

    def book(self) -> tuple[GrammarTopic, ...]:
        """Какую тетрадь показывать: грамматику изучаемого языка."""
        return self.context.language.grammar

    @property
    def topic(self) -> GrammarTopic:
        return self.topics[self.index]

    def on_show(self) -> None:
        self.render()  # заодно перекрашивает таблицы, если сменили тему оформления

    def show(self, index: int) -> None:
        """Открыть тему с этим номером (по кругу)."""
        self.index = index % len(self.topics)
        self.settings.set(self.index_setting, self.index)
        self.render()

    def render(self) -> None:
        topic = self.topic
        self.topic_place.configure(text=f"{topic.section.upper()} / ТЕМА {self.index + 1} ИЗ {len(self.topics)}")
        self.topic_title.configure(text=topic.title)
        self.intro.configure(text=topic.intro)
        for index, button in enumerate(self.topic_buttons):
            current = index == self.index
            button.configure(
                fg_color=theme.ACCENT_SOFT if current else "transparent",
                text_color=theme.ACCENT if current else theme.TEXT,
            )
        self._scroll_list_to_current()

        for child in self.scroll.winfo_children():  # убрать таблицы прошлой темы
            child.destroy()
        self.cells = []
        self._cell_columns = []
        self.tip = None
        self._draw_leading()
        for table in topic.tables:
            self._draw_table(table)
        if topic.tip:
            self.tip = Muted(
                self.scroll,
                f"Совет: {topic.tip}",
                font=theme.BODY,
                text_color=theme.ACCENT,
                wraplength=self._text_width - 30,
            )
            self.tip.pack(anchor="w", pady=(6, 12))
        self.scroll._parent_canvas.yview_moveto(0)  # новая тема - с самого верха

    def _scroll_list_to_current(self) -> None:
        """Прокрутить оглавление так, чтобы кнопка текущей темы была видна.

        Холст прокрутки считает положение долями: 0 - самый верх списка,
        1 - самый низ. yview() возвращает видимый кусок, например (0.4, 0.7).
        Если кнопка внутри этого куска - ничего не трогаем: иначе список
        прыгал бы при каждом щелчке мышью.
        """
        self.topic_list.update_idletasks()  # чтобы положения кнопок были посчитаны
        height = self.topic_list.winfo_height()
        if height <= 1:  # страница ещё не нарисована
            return
        button = self.topic_buttons[self.index]
        canvas = self.topic_list._parent_canvas
        top, bottom = canvas.yview()
        start = button.winfo_y() / height
        end = (button.winfo_y() + button.winfo_height()) / height
        if start < top or end > bottom:
            # Кнопку ставим примерно на треть видимой части сверху.
            canvas.yview_moveto(max(0.0, start - (bottom - top) / 3))

    def _draw_table(self, table: Table) -> None:
        """Таблица из обычных меток tkinter.

        Рамка таблицы залита цветом линий, а клетки стоят с зазором в 1 пиксель:
        сквозь зазоры видна заливка - получаются тонкие линии сетки.
        """
        if table.title:
            SectionLabel(self.scroll, "", table.title).pack(anchor="w", pady=(10, 4))
        scale = ctk.ScalingTracker.get_widget_scaling(self)
        size = round(14 * scale)
        font = (theme.FONT, -size)
        bold = (theme.FONT_SEMIBOLD, -size)
        grid = tk.Frame(self.scroll, bg=theme.pick(theme.LINE_STRONG))
        grid.pack(anchor="w", pady=(0, 14))

        for column, header in enumerate(table.headers):
            self._cell(grid, header, 0, column, bold, theme.CARD_ALT, theme.MUTED, scale, len(table.headers))
        for row_index, row in enumerate(table.rows, start=1):
            for column, text in enumerate(row):
                speakable = column in table.speak_columns and text != "-"
                color = theme.ACCENT if speakable else theme.TEXT
                cell = self._cell(grid, text, row_index, column, font, theme.CARD, color, scale, len(table.headers))
                if speakable:
                    cell.configure(cursor="hand2")
                    # t=text - каждая клетка "помнит" свой текст (ловушка с lambda в цикле).
                    cell.bind("<Button-1>", lambda event, t=text: self.voice.say(t))

    def _cell(self, grid, text, row, column, font, background, foreground, scale, columns) -> tk.Label:
        cell = tk.Label(
            grid,
            text=text,
            font=font,
            bg=theme.pick(background),
            fg=theme.pick(foreground),
            anchor="w",
            justify="left",
            padx=round(CELL_PADDING * scale),
            pady=round(7 * scale),
            wraplength=self._cell_wrap(columns),
        )
        cell.grid(row=row, column=column, sticky="nsew", padx=1, pady=1)
        self.cells.append(cell)
        self._cell_columns.append(columns)
        return cell

    def _draw_leading(self) -> None:
        """Перед таблицами темы подкласс может нарисовать что-то своё (по умолчанию - ничего)."""

    # --- клавиши ---------------------------------------------------------------------

    def on_key(self, key: KeyPress) -> bool:
        if key.is_("Down"):
            self.show(self.index + 1)
        elif key.is_("Up"):
            self.show(self.index - 1)
        else:
            return False
        return True

    def speak_text(self) -> str | None:
        # По клавише P звучит первый пример темы на изучаемом языке.
        table = self.topic.tables[0]
        return table.rows[0][table.speak_columns[0]] if table.speak_columns else None


class ToneChart(tk.Canvas):
    """График высоты голоса для четырёх тонов.

    Высота голоса показана как ноты: 5 уровней, 5 - самый высокий, 1 - низкий.
    Каждый тон - линия на этих уровнях. Контур показывает, куда идёт голос:
      1-й тон  - ровно наверху (5-5);
      2-й тон  - снизу вверх (3-5);
      3-й тон  - вниз и вверх (2-1-4);
      4-й тон  - сверху вниз (5-1).
    """

    TONES = (
        ("1-й тон", "ā", "mā", (5, 5)),
        ("2-й тон", "á", "má", (3, 5)),
        ("3-й тон", "ǎ", "mǎ", (2, 1, 4)),
        ("4-й тон", "à", "mà", (5, 1)),
    )
    LANE = 58  # высота полосы одного тона (логические единицы)
    PAD_TOP = 12
    PAD_BOTTOM = 14
    LABEL_W = 120  # место слева под номер и значок тона

    def __init__(self, master):
        self._scale = ctk.ScalingTracker.get_widget_scaling(master)
        self._width = round(480 * self._scale)
        self._height = round((self.PAD_TOP + self.PAD_BOTTOM + self.LANE * len(self.TONES)) * self._scale)
        super().__init__(
            master,
            width=self._width,
            height=self._height,
            highlightthickness=0,
            bg=theme.pick(theme.CARD),
        )
        self._draw()

    def _level_y(self, level: int, top: float, bottom: float) -> float:
        """Уровень высоты (1-5) в координату y: 5 - верх полосы, 1 - низ."""
        return top + (5 - level) / 4 * (bottom - top)

    def _draw(self) -> None:
        s = self._scale
        font = (theme.FONT, -round(14 * s))
        bold = (theme.FONT_SEMIBOLD, -round(14 * s))
        grid_color = theme.pick(theme.BORDER)
        accent = theme.pick(theme.ACCENT)
        text_color = theme.pick(theme.TEXT)
        faint = theme.pick(theme.FAINT)

        for i, (number, mark, pinyin, contour) in enumerate(self.TONES):
            top = (self.PAD_TOP + i * self.LANE) * s
            bottom = top + (self.LANE - 10) * s
            middle = (top + bottom) / 2
            # Пять направляющих - уровни высоты.
            for level in range(1, 6):
                y = self._level_y(level, top, bottom)
                self.create_line(0, y, self._width, y, fill=grid_color)
            # Линия тона.
            left = self.LABEL_W * s
            right = self._width - 16 * s
            points = []
            for j, level in enumerate(contour):
                x = left + j * (right - left) / (len(contour) - 1)
                points += [x, self._level_y(level, top, bottom)]
            self.create_line(*points, fill=accent, width=round(3 * s), smooth=True, capstyle="round")
            # Подписи слева.
            self.create_text(14 * s, middle, text=number, font=bold, fill=accent, anchor="w")
            self.create_text(66 * s, middle, text=mark, font=font, fill=text_color, anchor="w")
            self.create_text(left - 10 * s, middle, text=pinyin, font=font, fill=faint, anchor="e")


class SoundsPage(GrammarPage):
    """Китайские "Звуки и тоны": тоны, пиньинь, первые иероглифы.

    Стоит в меню на месте английской азбуки (тот же ключ "alphabet"):
    у китайского нет букв, и начинают его с тонов и звуков.
    """

    key = "alphabet"
    title = "Звуки и тоны"
    tagline = "С чего начинается китайский."
    index_setting = "sounds_index"

    def book(self) -> tuple[GrammarTopic, ...]:
        return self.context.language.sounds

    def _draw_leading(self) -> None:
        """Перед таблицами темы "Четыре тона" рисуем график высоты голоса."""
        if self.topic.title == "Четыре тона":
            ToneChart(self.scroll).pack(anchor="w", pady=(8, 14))
