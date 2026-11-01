# =============================================================================
# ОБЩИЕ ЭЛЕМЕНТЫ ИНТЕРФЕЙСА - "кубики", из которых собираются страницы
# =============================================================================
#
# Что это в жизни: "детали конструктора" одного стиля. Box - простая рамка,
# Card - карточка со скруглёнными углами, AccentButton и GhostButton -
# кнопки, StatCard - плитка с числом, RichText - текст с разным оформлением
# (словарь, справка). Страницы собираются из этих деталей.
#
# Каждый элемент - класс-наследник готового виджета CustomTkinter.
# Наследуемся, чтобы один раз задать оформление и больше не повторять
# одни и те же параметры (corner_radius, fg_color, ...) на каждой странице.

import tkinter as tk

import customtkinter as ctk

from gui import theme


class Box(tk.Frame):
    """Лёгкая рамка для раскладки элементов (ничего не рисует сама).

    Зачем: прозрачная рамка CustomTkinter внутри - это холст размером со
    всю рамку, и при растягивании окна он перерисовывается целиком.
    Пять вложенных таких рамок перерисовывались 125 мс, а пять обычных
    рамок tkinter - 12 мс. Поэтому для рамок, которые только раскладывают
    элементы по местам, используем обычную tk.Frame.

    Чтобы она вела себя как рамка CustomTkinter, добавляем три вещи:
      1. цвет фона - пара (светлая тема, тёмная тема), меняется вместе с темой;
      2. cget("bg") возвращает эту пару: элементы CustomTkinter внутри Box
         берут цвет фона у родителя именно так и сами перекрашиваются при смене темы;
      3. отступы (padx, pady) и размеры увеличиваются по масштабу экрана (125%, 200%).
    """

    def __init__(self, master, color: tuple[str, str] = theme.BG, width: int = 0, height: int = 0):
        self._color = color
        scale = ctk.ScalingTracker.get_widget_scaling(master)
        super().__init__(
            master, bg=theme.pick(color), bd=0, highlightthickness=0, width=round(width * scale), height=round(height * scale)
        )
        # Трекер тем CustomTkinter вызовет _on_appearance при смене темы.
        ctk.AppearanceModeTracker.add(self._on_appearance, self)

    def _on_appearance(self, mode: str) -> None:
        if self.winfo_exists():
            super().configure(bg=self._color[1] if mode.lower() == "dark" else self._color[0])

    def cget(self, key):
        if key in ("bg", "background"):
            return self._color
        return super().cget(key)

    def _scaled(self, kwargs: dict) -> dict:
        scale = ctk.ScalingTracker.get_widget_scaling(self)
        for key in ("padx", "pady", "ipadx", "ipady", "x", "y"):
            value = kwargs.get(key)
            if isinstance(value, (int, float)):
                kwargs[key] = round(value * scale)
            elif isinstance(value, tuple):
                kwargs[key] = tuple(round(v * scale) for v in value)
        return kwargs

    def pack(self, **kwargs):
        return super().pack(**self._scaled(kwargs))

    def grid(self, **kwargs):
        return super().grid(**self._scaled(kwargs))

    def place(self, **kwargs):
        return super().place(**self._scaled(kwargs))


class Card(ctk.CTkFrame):
    """Белая (или тёмная) карточка со скруглёнными углами."""

    def __init__(self, master, **kwargs):
        # **kwargs - "все остальные именованные аргументы". Передаём их
        # родителю как есть: так Card принимает всё, что принимает CTkFrame.
        kwargs.setdefault("fg_color", theme.CARD)
        kwargs.setdefault("corner_radius", 16)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", theme.BORDER)
        super().__init__(master, **kwargs)


class Title(ctk.CTkLabel):
    """Заголовок блока."""

    def __init__(self, master, text: str, font=theme.H1, **kwargs):
        super().__init__(master, text=text, font=font, text_color=theme.TEXT, anchor="w", **kwargs)


class Muted(ctk.CTkLabel):
    """Серый поясняющий текст."""

    def __init__(self, master, text: str = "", font=theme.BODY, **kwargs):
        kwargs.setdefault("anchor", "w")
        kwargs.setdefault("justify", "left")
        kwargs.setdefault("text_color", theme.MUTED)
        super().__init__(master, text=text, font=font, **kwargs)


class SectionLabel(ctk.CTkLabel):
    """Метка раздела моноширинным шрифтом: "01 / КАРТОЧКИ".

    Так подписаны разделы на сайте-образце: номер, косая черта и название
    заглавными буквами - как комментарий в коде.
    """

    def __init__(self, master, number: int | str, text: str, color=theme.FAINT, **kwargs):
        # number=3 даёт "03 / ТЕКСТ", number="" - просто "ТЕКСТ" (метка без номера).
        if isinstance(number, int):
            label = f"{number:02d} / {text.upper()}"
        else:
            label = f"{number} / {text.upper()}" if number else text.upper()
        kwargs.setdefault("anchor", "w")
        super().__init__(master, text=label, font=theme.LABEL, text_color=color, **kwargs)


class PageHeader(Box):
    """Шапка страницы в стиле сайта.

        01 / КАРТОЧКИ
        Карточки. Слово за словом.      <- вторая часть курсивом в цвет акцента
        Поясняющий текст серым.
    """

    def __init__(
        self,
        master,
        number: int,
        title: str,
        tagline: str = "",
        description: str = "",
        hero: bool = False,
        label: str = "",
    ):
        """label - текст метки над заголовком (по умолчанию - сам заголовок)."""
        super().__init__(master, color=theme.BG)
        SectionLabel(self, number, label or title.rstrip(".")).pack(anchor="w")
        line = Box(self, color=theme.BG)
        line.pack(anchor="w", pady=(4, 0))
        font, accent_font = (theme.HERO, theme.HERO_ACCENT) if hero else (theme.H1, theme.H1_ACCENT)
        ctk.CTkLabel(line, text=title, font=font, text_color=theme.TEXT).pack(side="left")
        if tagline:
            ctk.CTkLabel(line, text=" " + tagline, font=accent_font, text_color=theme.ACCENT).pack(side="left")
        self.description = Muted(self, description)
        if description:
            self.description.pack(anchor="w", pady=(2, 0))


class AccentButton(ctk.CTkButton):
    """Основная кнопка: "таблетка" цвета акцента с тёмным текстом."""

    def __init__(self, master, text: str, command=None, **kwargs):
        kwargs.setdefault("fg_color", theme.ACCENT)
        kwargs.setdefault("hover_color", theme.ACCENT_HOVER)
        kwargs.setdefault("text_color", theme.ON_ACCENT)
        kwargs.setdefault("height", 42)
        kwargs.setdefault("corner_radius", 21)  # половина высоты - полностью круглые края
        kwargs.setdefault("font", theme.BODY_BOLD)
        super().__init__(master, text=text, command=command, **kwargs)


class GhostButton(ctk.CTkButton):
    """Второстепенная кнопка: прозрачная "таблетка" с тонкой рамкой."""

    def __init__(self, master, text: str, command=None, **kwargs):
        kwargs.setdefault("fg_color", "transparent")
        kwargs.setdefault("hover_color", theme.CARD_ALT)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", theme.LINE_STRONG)
        kwargs.setdefault("text_color", theme.TEXT)
        kwargs.setdefault("height", 42)
        kwargs.setdefault("corner_radius", 21)
        kwargs.setdefault("font", theme.BODY)
        super().__init__(master, text=text, command=command, **kwargs)


class SpeakButton(GhostButton):
    """Кнопка "Произнести". Обычный щелчок: нормальная скорость."""

    def __init__(self, master, command, text: str = "Произнести (P)", **kwargs):
        kwargs.setdefault("height", 34)
        kwargs.setdefault("corner_radius", 17)
        kwargs.setdefault("width", 190)
        kwargs.setdefault("font", theme.SMALL)
        kwargs.setdefault("text_color", theme.ACCENT)
        super().__init__(master, text, command, **kwargs)


class StatCard(Card):
    """Карточка с одним числом: метка "ВЫУЧЕНО" и крупное число под ней."""

    def __init__(self, master, title: str, color=theme.ACCENT):
        super().__init__(master)
        ctk.CTkLabel(self, text=title.upper(), font=theme.LABEL, text_color=theme.FAINT, anchor="w").pack(
            anchor="w", padx=20, pady=(16, 0)
        )
        self.value_label = ctk.CTkLabel(self, text="0", font=(theme.DISPLAY, 32), text_color=color)
        self.value_label.pack(anchor="w", padx=20, pady=(0, 14))

    def set(self, value) -> None:
        self.value_label.configure(text=str(value))


class RichText(Card):
    """Текстовое поле с цветной разметкой - быстрая замена сотням отдельных меток.

    Каждый виджет CustomTkinter - это маленький холст, который рисуется
    отдельно. 300 меток в словаре создавались и перерисовывались больше
    секунды. Обычное текстовое поле tkinter (tk.Text) показывает тот же
    текст за миллисекунды: оформление задаётся "тегами" (tag) - именованными
    стилями для кусочков текста, как стили в Word.

    Пример:
        box.define("bold", font=theme.BODY_BOLD, fg=theme.TEXT)
        box.write([("variable", "bold"), ("  переменная\n", "normal")])
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.text = tk.Text(self, wrap="word", bd=0, highlightthickness=0, cursor="arrow", undo=False)
        self.scrollbar = ctk.CTkScrollbar(self, command=self.text.yview, button_color=theme.BORDER)
        self.text.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y", padx=(0, 6), pady=12)
        self.text.pack(side="left", fill="both", expand=True, padx=(18, 4), pady=14)
        self.text.configure(state="disabled")  # только для чтения, но выделять и копировать можно
        self._styles: dict[str, dict] = {}

    # --- размеры с учётом масштаба экрана -------------------------------------
    # CustomTkinter сам увеличивает свои виджеты на экранах с масштабом 150-200%.
    # Обычный tk.Text этого не умеет, поэтому пересчитываем размеры сами.

    def px(self, size: float) -> int:
        return round(size * self._get_widget_scaling())

    def _font(self, spec: tuple) -> tuple:
        family, size, *rest = spec
        return (family, -self.px(size), *rest)  # минус: размер в пикселях, а не в пунктах

    # --- стили ------------------------------------------------------------------

    def define(self, name: str, font=None, fg=None, bg=None, **options) -> None:
        """Задать стиль (тег). Цвета - пары (светлая, тёмная) из theme."""
        self._styles[name] = {"font": font, "fg": fg, "bg": bg, **options}
        self._apply(name)

    def _apply(self, name: str) -> None:
        style = dict(self._styles[name])
        config = {}
        if style.pop("font"):
            config["font"] = self._font(self._styles[name]["font"])
        fg, bg = style.pop("fg"), style.pop("bg")
        if fg:
            config["foreground"] = theme.pick(fg)
        if bg:
            config["background"] = theme.pick(bg)
        for key, value in style.items():  # отступы и интервалы - тоже с учётом масштаба
            config[key] = self.px(value) if isinstance(value, (int, float)) else value
        self.text.tag_configure(name, **config)

    def restyle(self) -> None:
        """Перекрасить под текущую тему (светлую или тёмную)."""
        self.text.configure(
            background=theme.pick(theme.CARD),
            foreground=theme.pick(theme.TEXT),
            selectbackground=theme.pick(theme.ACCENT_SOFT),
            selectforeground=theme.pick(theme.TEXT),
            font=self._font(theme.BODY),
        )
        for name in self._styles:
            self._apply(name)

    # --- содержимое -------------------------------------------------------------

    def write(self, chunks: list[tuple[str, str | tuple[str, ...]]]) -> None:
        """Заменить весь текст. chunks - список (текст, тег или кортеж тегов)."""
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        for chunk, tags in chunks:
            self.text.insert("end", chunk, tags)
        self.text.configure(state="disabled")
        self.text.yview_moveto(0)
