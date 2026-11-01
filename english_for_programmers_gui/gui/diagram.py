# =============================================================================
# АНИМИРОВАННАЯ СХЕМА для главной страницы: как в тренажёре учится слово
# =============================================================================
#
# Три "стеклянные" плоскости - три шага изучения слова:
#
#   СЛОВО     - по буквам печатается английское слово (с мигающим курсором);
#   ПЕРЕВОД   - под светящимся ядром проявляется перевод;
#   ПРАКТИКА  - загораются три точки: три верных ответа, после которых слово
#               считается выученным (как в Progress.LEARNED_AFTER). Потом точки
#               становятся мятными - "выучено", и начинается следующее слово.
#
# Вокруг медленно плавают слова, которые пользователь сейчас учит. Их передаёт
# страница через set_words() - схема показывает настоящий словарь, а не картинку.
#
# Как это сделано в tkinter, где нет прозрачности и размытия:
#   - свечение - несколько колец, цвет которых плавно переходит от яркого
#     к цвету фона (theme.mix); "проявление" текста - то же смешивание цветов;
#   - анимация - метод _tick() каждые 40 мс (25 кадров в секунду) только
#     меняет уже нарисованные фигуры (coords, itemconfigure). Заново всё
#     рисуется лишь при изменении размера или смене темы;
#   - схема работает только пока видна: start() и stop() вызывает страница.

import math
import random
import tkinter as tk

import customtkinter as ctk

from gui import theme

# Слова на случай, если страница ещё ничего не передала.
DEFAULT_WORDS = [
    ("variable", "переменная"),
    ("however", "однако"),
    ("feature", "функция, возможность"),
    ("reliable", "надёжный"),
    ("deploy", "развернуть"),
    ("meanwhile", "тем временем"),
]


class LearningDiagram(tk.Canvas):
    FRAME_MS = 40
    LABELS = ("СЛОВО", "ПЕРЕВОД", "ПРАКТИКА")  # сверху вниз
    FLOATING = 5  # сколько слов плавает вокруг схемы
    TRAIL = 6  # сколько точек в "хвосте" сигнала на орбите
    STEPS = 3  # верных ответов до "выучено"

    # Расписание одного цикла (в секундах): когда что происходит.
    TYPE_END = 1.6  # слово допечатано
    TRANSLATE_END = 2.6  # перевод проявился
    DOT_EVERY = 0.7  # пауза между точками "верный ответ"
    LEARNED_AT = TRANSLATE_END + STEPS * DOT_EVERY  # все точки горят - "выучено"
    CYCLE = LEARNED_AT + 1.6  # длина цикла одного слова

    def __init__(self, master, **kwargs):
        super().__init__(master, highlightthickness=0, bd=0, **kwargs)
        self._frame = 0
        self._after_id = None
        self._geometry = None  # размеры фигур, считаются в _draw_static()
        self._words: list[tuple[str, str]] = list(DEFAULT_WORDS)
        self._floating_words: list[str] = []
        self._cycle_word = 0  # какое слово сейчас "изучается" в схеме
        self.bind("<Configure>", lambda event: self.redraw())

    # --- управление ------------------------------------------------------------

    def set_words(self, words: list[tuple[str, str]]) -> None:
        """Слова для схемы: [(английское, русское), ...]. Обычно - те, что сейчас учат."""
        self._words = list(words) or list(DEFAULT_WORDS)
        random.shuffle(self._words)
        self._floating_words = [en for en, _ in self._words[: self.FLOATING]]
        self._cycle_word = 0

    def start(self) -> None:
        if self._after_id is None:
            self._tick()

    def stop(self) -> None:
        if self._after_id is not None:
            self.after_cancel(self._after_id)
            self._after_id = None

    def redraw(self) -> None:
        """Перерисовать всё заново: при изменении размера и смене темы."""
        self.delete("all")
        self.configure(bg=theme.pick(theme.PANEL))
        if self.winfo_width() > 60 and self.winfo_height() > 60:
            self._draw_static()
            self._animate()

    # --- цвета текущей темы -----------------------------------------------------

    @staticmethod
    def _c(color: tuple[str, str]) -> str:
        return theme.pick(color)

    def _shade(self, amount: float, color=theme.ACCENT) -> str:
        """Цвет, смешанный с фоном панели: 0 - фон, 1 - чистый цвет."""
        amount = max(0.0, min(1.0, amount))
        return theme.mix(self._c(theme.PANEL), self._c(color), amount)

    # --- статичная часть ---------------------------------------------------------

    def _draw_static(self) -> None:
        w, h = self.winfo_width(), self.winfo_height()
        s = ctk.ScalingTracker.get_widget_scaling(self)
        cx, cy = w * 0.46, h * 0.52
        # Три плоскости целиком помещаются по высоте:
        # от верха верхней до низа нижней = 2 * step + 2 * b = 5.2 * b = 2.2 * a.
        a = min(w * 0.24, h * 0.39)  # половина ширины плоскости-ромба
        b = a * 0.42  # половина высоты ромба (вид сбоку под углом)
        step = b * 1.6  # расстояние между плоскостями
        levels = [cy - step, cy, cy + step]  # центры плоскостей: верх, середина, низ
        self._geometry = dict(w=w, h=h, s=s, cx=cx, a=a, b=b, levels=levels)

        self._draw_grid(w, h, s)
        self._draw_glow(cx, cy, a * 1.6, rings=14, strength=0.22, color=theme.ACCENT_STRONG)

        # Плоскости рисуем снизу вверх: верхняя ложится поверх нижних.
        fills = [theme.PLANE_TOP, theme.PLANE_MID, theme.PLANE_LOW]
        for index in (2, 1, 0):
            y = levels[index]
            if index < 2:  # светящаяся связь с плоскостью ниже
                self._glow_line(cx, y, cx, levels[index + 1], s)
            self._plane(cx, y, a, b, fills[index], s)
            self._label(cx + a, y, self.LABELS[index], s)

        # Орбита вокруг средней плоскости - тонкий эллипс.
        top, mid, low = levels
        self.create_oval(cx - a * 1.18, mid - b * 1.25, cx + a * 1.18, mid + b * 1.25, outline=self._shade(0.28), width=1)

        # --- подвижные фигуры: создаём один раз, в _animate() только меняем ---
        mono = (theme.MONO, -round(15 * s))
        small = (theme.FONT, -round(12 * s))

        self._core = [self.create_oval(0, 0, 0, 0, outline="", fill=self._shade(t)) for t in (0.12, 0.25, 0.45, 0.7)]
        self._core_center = self.create_oval(0, 0, 0, 0, outline="", fill=self._c(theme.HIGHLIGHT))
        self._trail = [self.create_oval(0, 0, 0, 0, outline="", fill=self._shade(1 - i / self.TRAIL)) for i in range(self.TRAIL)]
        self._trail.reverse()  # хвост рисуем первым, яркую голову - последней (поверх)

        # СЛОВО: печатающееся слово и курсор на верхней плоскости.
        self._typed = self.create_text(cx, top, text="", font=mono, fill=self._c(theme.HIGHLIGHT))
        self._caret = self.create_line(0, 0, 0, 0, width=max(1, round(1.5 * s)), fill=self._c(theme.ACCENT))
        # ПЕРЕВОД: текст под ядром на средней плоскости.
        self._translation = self.create_text(cx, mid + b * 0.52, text="", font=small, fill=self._c(theme.PANEL))
        # ПРАКТИКА: три точки на нижней плоскости.
        gap = a * 0.22
        r = 4.5 * s
        self._dots = [
            self.create_oval(cx + (i - 1) * gap - r, low - r, cx + (i - 1) * gap + r, low + r, outline="", fill=self._shade(0.2))
            for i in range(self.STEPS)
        ]
        # Слова, которые плавают вокруг схемы.
        self._floating = [
            self.create_text(0, 0, text=word, font=(theme.FONT, -round(12 * s)), fill=self._shade(0.42), anchor="center")
            for word in self._floating_words
        ]

    def _draw_grid(self, w: int, h: int, s: float) -> None:
        step = round(26 * s)
        color = self._shade(0.07, theme.TEXT)
        for x in range(0, w, step):
            self.create_line(x, 0, x, h, fill=color)
        for y in range(0, h, step):
            self.create_line(0, y, w, y, fill=color)

    def _draw_glow(self, x: float, y: float, radius: float, rings: int, strength: float, color) -> None:
        """Мягкое пятно света: кольца от фона к цвету, от большого к маленькому."""
        for i in range(rings):
            r = radius * (1 - i / rings)
            amount = strength * ((i + 1) / rings) ** 1.6
            self.create_oval(x - r, y - r * 0.55, x + r, y + r * 0.55, outline="", fill=self._shade(amount, color))

    def _plane(self, cx: float, y: float, a: float, b: float, fill, s: float) -> None:
        """Ромб-плоскость с "стеклянным" бликом по верхним граням."""
        points = (cx - a, y, cx, y - b, cx + a, y, cx, y + b)
        self.create_polygon(points, fill=self._c(fill), outline=self._c(theme.PLANE_EDGE), width=max(1, round(s)))
        self.create_line(cx - a, y, cx, y - b, cx + a, y, fill=self._shade(0.55), width=max(1, round(1.2 * s)))
        k = 0.82  # внутренняя рамка - ощущение толщины стекла
        inner = (cx - a * k, y, cx, y - b * k, cx + a * k, y, cx, y + b * k)
        self.create_polygon(inner, fill="", outline=self._shade(0.18), width=1)

    def _glow_line(self, x1, y1, x2, y2, s: float) -> None:
        for width, amount in ((10, 0.08), (6, 0.18), (3, 0.4), (1.4, 0.95)):
            self.create_line(x1, y1, x2, y2, width=max(1, round(width * s)), fill=self._shade(amount), capstyle="round")

    def _label(self, x: float, y: float, text: str, s: float) -> None:
        gap = 14 * s
        self.create_line(x + gap * 0.4, y, x + gap * 2.2, y, fill=self._shade(0.45))
        self.create_oval(x - 3 * s, y - 3 * s, x + 3 * s, y + 3 * s, outline="", fill=self._shade(0.9))
        self.create_text(x + gap * 2.6, y, text=text, anchor="w", font=(theme.MONO, -round(11 * s)), fill=self._shade(0.85))

    # --- анимация ---------------------------------------------------------------

    def _tick(self) -> None:
        self._frame += 1
        self._animate()
        self._after_id = self.after(self.FRAME_MS, self._tick)

    def _animate(self) -> None:
        g = self._geometry
        if not g or not self.find_all():
            return
        t = self._frame * self.FRAME_MS / 1000  # секунды с начала анимации
        self._animate_core(t, g)
        self._animate_orbit(t, g)
        self._animate_word(t, g)
        self._animate_floating(t, g)

    def _animate_core(self, t: float, g: dict) -> None:
        """Ядро "дышит": размер и яркость меняются по синусоиде (период ~3 с)."""
        cx, mid, s = g["cx"], g["levels"][1], g["s"]
        breathe = 0.5 + 0.5 * math.sin(t * 2.1)
        base = (5 + 2 * breathe) * s
        for i, ring in enumerate(self._core):
            r = base * (4.2 - i * 0.9)
            self.coords(ring, cx - r, mid - r * 0.7, cx + r, mid + r * 0.7)
        r = base * 0.9
        self.coords(self._core_center, cx - r, mid - r, cx + r, mid + r)

    def _animate_orbit(self, t: float, g: dict) -> None:
        """Сигнал бежит по орбите, за ним тянется затухающий хвост."""
        cx, mid, a, b, s = g["cx"], g["levels"][1], g["a"], g["b"], g["s"]
        rx, ry = a * 1.18, b * 1.25
        for i, dot in enumerate(self._trail):
            angle = t * 1.6 - (self.TRAIL - 1 - i) * 0.09
            x, y = cx + rx * math.cos(angle), mid + ry * math.sin(angle)
            size = (1.5 + 3.0 * (i + 1) / self.TRAIL) * s
            self.coords(dot, x - size, y - size, x + size, y + size)

    def _animate_word(self, t: float, g: dict) -> None:
        """Цикл одного слова: печать, перевод, три верных ответа, "выучено"."""
        cycle = int(t // self.CYCLE)
        phase = t % self.CYCLE  # секунды от начала цикла текущего слова
        en, ru = self._words[(self._cycle_word + cycle) % len(self._words)]
        ru = self._short(ru)
        top, mid = g["levels"][0], g["levels"][1]

        # СЛОВО: печатается по буквам, в конце цикла гаснет.
        shown = en[: round(len(en) * min(1.0, phase / self.TYPE_END))]
        fade_out = max(0.0, (phase - (self.CYCLE - 0.5)) / 0.5)  # последние 0.5 с - затухание
        self.itemconfigure(self._typed, text=shown, fill=self._shade(1 - fade_out, theme.HIGHLIGHT))
        # Курсор стоит после последней буквы и мигает (2 раза в секунду).
        box = self.bbox(self._typed)
        caret_x = box[2] + 3 * g["s"] if box and shown else g["cx"]
        caret_on = int(t * 4) % 2 == 0 and fade_out == 0
        h = 9 * g["s"]
        self.coords(self._caret, caret_x, top - h, caret_x, top + h)
        self.itemconfigure(self._caret, fill=self._shade(1.0 if caret_on else 0.0))

        # ПЕРЕВОД: плавно проявляется после того, как слово допечатано.
        appear = (phase - self.TYPE_END) / (self.TRANSLATE_END - self.TYPE_END)
        self.itemconfigure(self._translation, text=ru, fill=self._shade(min(1.0, appear) * (1 - fade_out), theme.TEXT))

        # ПРАКТИКА: точки загораются одна за другой, потом все становятся мятными.
        learned = phase >= self.LEARNED_AT
        for i, dot in enumerate(self._dots):
            lit = phase >= self.TRANSLATE_END + (i + 1) * self.DOT_EVERY
            if learned:
                color = self._shade(1 - fade_out * 0.8, theme.SUCCESS)
            elif lit:
                color = self._shade(1.0)
            else:
                color = self._shade(0.2)
            self.itemconfigure(dot, fill=color)

    def _animate_floating(self, t: float, g: dict) -> None:
        """Слова медленно плавают вверх-вниз; раз в 7 секунд одно сменяется другим."""
        cx, a, b, s = g["cx"], g["a"], g["b"], g["s"]
        top, mid, low = g["levels"]
        # Места слов: (сдвиг по горизонтали в ширинах плоскости, высота) - все внутри схемы.
        spots = [(-1.35, top - b * 0.5), (1.75, top - b * 1.05), (-1.5, mid + b * 0.95), (1.85, low + b * 0.95), (-1.25, low + b * 0.6)]
        swap_every = 7.0
        swapping = int(t // swap_every) % len(self._floating)  # какое слово сейчас меняется
        swap_phase = (t % swap_every) / swap_every
        for i, (item, (dx, y)) in enumerate(zip(self._floating, spots)):
            self.coords(item, cx + a * dx, y + math.sin(t * 1.1 + i * 1.7) * 5 * s)
            brightness = 0.42
            if i == swapping:
                # Плавно гаснет, меняется на другое слово и снова загорается.
                fade = abs(math.cos(swap_phase * math.pi))
                brightness *= fade
                if swap_phase > 0.5 and self.itemcget(item, "text") == self._floating_words[i]:
                    # Берём слово, которого сейчас нет среди плавающих, - без повторов.
                    choices = [en for en, _ in self._words if en not in self._floating_words] or [self._words[0][0]]
                    new_word = random.choice(choices)
                    self._floating_words[i] = new_word
                    self.itemconfigure(item, text=new_word)
            self.itemconfigure(item, fill=self._shade(brightness))

    @staticmethod
    def _short(ru: str) -> str:
        """Короткий перевод для схемы: до первой запятой, точки с запятой или скобки."""
        for separator in (";", ",", "("):
            ru = ru.split(separator)[0]
        return ru.strip()
