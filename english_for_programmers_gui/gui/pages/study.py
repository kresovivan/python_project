# =============================================================================
# СТРАНИЦЫ ЗАНЯТИЙ - карточки, выбор перевода, написание слова
# =============================================================================
#
#   Page
#   `-- StudyPage (абстрактный: экраны, полоска, итог, общие клавиши)
#       |-- CardsPage   - "знаю / не знаю"
#       |-- ChoicePage  - выбрать перевод из 4 вариантов
#       `-- TypingPage  - написать слово по-английски
#
# Вся логика занятия (какие слова, счёт, место остановки) - в классе Lesson
# (core/lesson.py). Страница только показывает слова и передаёт ответы.
# Наследники пишут build_body() и render() - как выглядит упражнение
# и как показать одно слово - и, если нужно, handle_key().

import random
from abc import ABC, abstractmethod

import customtkinter as ctk

from core.answers import AnswerChecker
from core.lesson import Lesson
from core.models import Word
from core.session import Session
from gui import theme
from gui.context import AppContext
from gui.hotkeys import KeyPress
from gui.pages.base import Page
from gui.widgets import AccentButton, Box, Card, GhostButton, Muted, SpeakButton


class StudyPage(Page, ABC):
    # Page, ABC - множественное наследование: StudyPage - это страница (Page)
    # и одновременно абстрактный класс (ABC). Создать StudyPage() напрямую
    # нельзя - только наследников, которые написали build_body() и render().
    AUTO_NEXT_MS = 900  # пауза перед следующим словом после верного ответа

    def __init__(self, master, context: AppContext):
        super().__init__(master, context)
        self.lesson = Lesson(self.key, self.vocabulary, self.progress, self.settings)
        self.word: Word | None = None  # слово на экране
        self._after_id = None  # отложенный переход к следующему слову
        self._screen = None  # какой экран виден: intro, body или result

        self._build_header()
        self.screen = Card(self)
        self.screen.pack(fill="both", expand=True, pady=(18, 0))
        # Три "экрана" в одном месте: приглашение, упражнение, итог.
        self.intro = Box(self.screen, color=theme.CARD)
        self.intro_label = Muted(self.intro, font=theme.H3, anchor="center", justify="center", wraplength=600)
        self.intro_label.pack(expand=True)
        self.body = Box(self.screen, color=theme.CARD)
        self.build_body(self.body)
        self.result = Box(self.screen, color=theme.CARD)
        self._build_result()

    # === методы, которые пишут наследники =====================================

    @abstractmethod
    def build_body(self, parent) -> None:
        """Создать элементы упражнения (один раз)."""

    @abstractmethod
    def render(self, word: Word) -> None:
        """Показать очередное слово."""

    def handle_key(self, key: KeyPress) -> bool:
        """Клавиши во время упражнения. Наследники переопределяют."""
        return False

    # === удобные свойства =====================================================

    @property
    def session(self) -> Session | None:
        return self.lesson.session

    @property
    def topics(self) -> list[str]:
        return self.lesson.topics

    # === построение ===========================================================

    def _build_header(self) -> None:
        self.build_header()

        toolbar = Box(self, color=theme.BG)
        toolbar.pack(fill="x", pady=(16, 0))
        self.topic_menu = ctk.CTkOptionMenu(
            toolbar,
            values=self.lesson.topics,
            width=380,
            height=40,
            corner_radius=12,
            font=theme.BODY,
            dropdown_font=theme.BODY,
            fg_color=theme.CARD_ALT,
            button_color=theme.ACCENT,
            button_hover_color=theme.ACCENT_HOVER,
            text_color=theme.TEXT,
            dynamic_resizing=False,
        )
        self.topic_menu.set(self.lesson.last_topic)
        self.topic_menu.pack(side="left")
        AccentButton(toolbar, "Новое занятие    Ctrl+N", self.start_new, width=230).pack(side="left", padx=12)
        Muted(toolbar, "CTRL+ВВЕРХ/ВНИЗ: СМЕНИТЬ ТЕМУ", font=theme.LABEL, text_color=theme.FAINT).pack(side="left", padx=6)

        status = Box(self, color=theme.BG)
        status.pack(fill="x", pady=(18, 10))
        self.counter = Muted(status, font=theme.LABEL, text_color=theme.FAINT)
        self.counter.pack(side="left")
        self.score = Muted(status, font=theme.LABEL, text_color=theme.FAINT)
        self.score.pack(side="right")
        # Тонкая линия прогресса, как на сайте-образце.
        self.bar = ctk.CTkProgressBar(
            self, height=3, corner_radius=2, fg_color=theme.BORDER, progress_color=theme.ACCENT
        )
        self.bar.pack(fill="x")
        self.bar.set(0)

    def _build_result(self) -> None:
        box = Box(self.result, color=theme.CARD)
        box.pack(expand=True)
        self.result_title = ctk.CTkLabel(box, text="", font=theme.H1, text_color=theme.TEXT)
        self.result_title.pack(pady=(0, 6))
        self.result_score = ctk.CTkLabel(box, text="", font=(theme.DISPLAY, 64), text_color=theme.ACCENT)
        self.result_score.pack()
        self.result_text = Muted(box, anchor="center", justify="center")
        self.result_text.pack(pady=(4, 24))
        buttons = Box(box, color=theme.CARD)
        buttons.pack()
        AccentButton(buttons, "Ещё занятие    Enter", self.start_new, width=210).pack(side="left", padx=6)
        self.retry_button = GhostButton(buttons, "Повторить ошибки    Ctrl+R", self.retry_mistakes, width=250)
        self.retry_button.pack(side="left", padx=6)
        GhostButton(buttons, "На главную    Esc", lambda: self.navigator.show_page("home"), width=180).pack(
            side="left", padx=6
        )

    # === экраны ===============================================================

    def _show_screen(self, frame) -> None:
        for child in (self.intro, self.body, self.result):
            child.pack_forget()
        frame.pack(fill="both", expand=True, padx=30, pady=18)
        self._screen = frame  # от видимого экрана зависят горячие клавиши

    def _show_intro(self, text: str | None = None) -> None:
        self.lesson.forget()
        self.counter.configure(text="")
        self.score.configure(text="")
        self.bar.set(0)
        self.intro_label.configure(text=text or self._intro_text())
        self._show_screen(self.intro)

    def _intro_text(self) -> str:
        return (
            f"Тема: {self.topic_menu.get()}\n\n"
            "Enter - начать занятие\n"
            "Ctrl+Вверх / Ctrl+Вниз: выбрать другую тему\n\n"
            f"В занятии {Lesson.SIZE} слов. F1 - все горячие клавиши."
        )

    # === жизненный цикл страницы ==============================================

    def on_show(self) -> None:
        if self.lesson.active:
            return  # занятие уже идёт на экране - ничего не трогаем
        if self.lesson.restore():
            self.topic_menu.set(self.session.topic)
            self.show_current()
        else:
            self._show_intro()

    def on_hide(self) -> None:
        self._cancel_pending()

    # === горячие клавиши ======================================================

    def on_key(self, key: KeyPress) -> bool:
        """Клавиши, общие для всех занятий. Остальное - в handle_key() наследника."""
        if key.ctrl and key.is_letter("N"):
            self.start_new()
        elif key.ctrl and key.is_("Up", "Down"):
            self.shift_topic(-1 if key.is_("Up") else 1)
        elif key.ctrl and key.is_letter("R") and self._screen is self.result:
            self.retry_mistakes()
        elif self._screen is self.intro and key.is_("Return"):
            self.start_new()
        elif self._screen is self.result and key.is_("Return", "space"):
            self.start_new()
        elif self._screen is self.body:
            return self.handle_key(key)
        else:
            return False
        return True

    # === действия =============================================================

    def shift_topic(self, step: int) -> None:
        """Выбрать соседнюю тему в списке (занятие не начинается само)."""
        topic = self.lesson.neighbour_topic(self.topic_menu.get(), step)
        self.topic_menu.set(topic)
        self.lesson.remember_topic(topic)
        if self._screen is self.intro:
            self.intro_label.configure(text=self._intro_text())

    def start_new(self) -> None:
        if self.lesson.start(self.topic_menu.get()):
            self.show_current()
        else:
            self._show_intro("Слабых слов пока нет - отличная работа!\n\nВыберите другую тему.")

    def retry_mistakes(self) -> None:
        if self.lesson.retry_mistakes():
            self.show_current()

    def show_current(self) -> None:
        self._cancel_pending()
        self.word = self.lesson.current_word()
        if self.word is None:
            self.show_result()
            return
        self._update_status()
        self._show_screen(self.body)
        self.render(self.word)
        # Заранее скачиваем произношение (в фоне): по P слово прозвучит сразу.
        self.voice.prefetch(self.word.answer)
        # Если включено "Произносить сразу" - слово звучит при показе.
        # В "Написании слова" speak_text() до ответа пустой, чтобы не выдать ответ.
        self.voice.auto_say(self.speak_text())

    def answer(self, is_right: bool) -> None:
        """Передать ответ занятию и обновить счёт на экране."""
        self.lesson.answer(self.word, is_right)
        self._update_status()

    def next_word(self) -> None:
        if self.session:
            self.show_current()

    def next_later(self, ms: int) -> None:
        """Перейти к следующему слову через ms миллисекунд."""
        self._cancel_pending()
        self._after_id = self.after(ms, self.next_word)

    def _cancel_pending(self) -> None:
        if self._after_id:
            self.after_cancel(self._after_id)
            self._after_id = None

    # === озвучка ==============================================================

    def speak_text(self) -> str | None:
        """По умолчанию по клавише P звучит текущее слово упражнения."""
        if self._screen is self.body and self.word:
            return self.word.answer
        return None

    def speak(self) -> None:
        self.voice.say(self.speak_text())

    # === отображение ==========================================================

    def _update_status(self) -> None:
        s = self.session
        shown = min(s.index + 1, s.total)
        self.counter.configure(text=f"{s.topic.upper()}  /  СЛОВО {shown} ИЗ {s.total}")
        self.score.configure(text=f"ВЕРНО {s.right}    ОШИБОК {s.wrong}")
        self.bar.set(s.fraction)

    def show_result(self) -> None:
        s = self.session
        if s.percent == 100:
            title = "Excellent! Отлично!"
        elif s.percent >= 70:
            title = "Good job! Хорошая работа!"
        else:
            title = "Keep going! Продолжайте!"
        self.result_title.configure(text=title)
        self.result_score.configure(text=f"{s.percent}%")
        self.result_text.configure(text=f"Верно: {s.right},   ошибок: {s.wrong},   всего: {s.answered}")
        self.retry_button.configure(state="normal" if s.mistakes else "disabled")
        self.counter.configure(text=f"{s.topic.upper()}  /  ЗАНЯТИЕ ЗАВЕРШЕНО")
        self.bar.set(1)
        self._show_screen(self.result)


# =============================================================================
# Карточки
# =============================================================================


class CardsPage(StudyPage):
    key = "cards"
    title = "Карточки"
    tagline = "Слово за словом."
    description = "Посмотрите на слово, вспомните перевод, откройте ответ и честно отметьте: знаете или нет."

    def build_body(self, parent) -> None:
        self.en_label = ctk.CTkLabel(parent, text="", font=theme.WORD, text_color=theme.TEXT)
        self.en_label.pack(pady=(24, 0))
        self.sound_label = Muted(parent, font=theme.SOUND, anchor="center")
        self.sound_label.pack()
        SpeakButton(parent, self.speak).pack(pady=(10, 0))

        self.ru_label = ctk.CTkLabel(parent, text="", font=theme.H2, text_color=theme.ACCENT, wraplength=700)
        self.example_label = Muted(parent, anchor="center", justify="center", wraplength=700)
        self.reveal_button = AccentButton(parent, "Показать перевод    Пробел / Enter", self.reveal, width=320)

        self.buttons = Box(parent, color=theme.CARD)
        self._answer_button("Не знаю (1)", False, theme.DANGER, theme.DANGER_HOVER, theme.ON_DANGER)
        self._answer_button("Знаю (2)", True, theme.SUCCESS, theme.SUCCESS_HOVER, theme.ON_SUCCESS)
        self.revealed = False

    def _answer_button(self, text: str, knows: bool, color, hover, text_color) -> None:
        ctk.CTkButton(
            self.buttons,
            text=text,
            command=lambda: self.mark(knows),
            fg_color=color,
            hover_color=hover,
            text_color=text_color,
            height=46,
            width=200,
            corner_radius=23,
            font=theme.BODY_BOLD,
        ).pack(side="left", padx=8)

    def render(self, word: Word) -> None:
        self.revealed = False
        self.en_label.configure(text=word.en)
        self.sound_label.configure(text=f"[ {word.sound} ]")
        self.ru_label.pack_forget()
        self.example_label.pack_forget()
        self.buttons.pack_forget()
        self.reveal_button.pack(pady=30)

    def reveal(self) -> None:
        if self.revealed:
            return
        self.revealed = True
        self.reveal_button.pack_forget()
        self.ru_label.configure(text=self.word.ru)
        self.ru_label.pack(pady=(22, 4))
        if self.word.example:
            self.example_label.configure(text=self.word.example)
            self.example_label.pack()
        self.buttons.pack(pady=22)

    def mark(self, knows: bool) -> None:
        if not self.revealed:
            return
        self.answer(knows)
        self.next_word()

    def handle_key(self, key: KeyPress) -> bool:
        if key.is_("space", "Return"):
            self.reveal()
        elif key.is_("1", "Left"):
            self.mark(False)
        elif key.is_("2", "Right"):
            self.mark(True)
        else:
            return False
        return True


# =============================================================================
# Выбор перевода
# =============================================================================


class ChoicePage(StudyPage):
    key = "choice"
    title = "Выбор перевода"
    tagline = "Один из четырёх."
    description = "Выберите правильный перевод. Можно мышью или клавишами 1-4."
    OPTIONS = 4

    def build_body(self, parent) -> None:
        self.en_label = ctk.CTkLabel(parent, text="", font=theme.WORD, text_color=theme.TEXT)
        self.en_label.pack(pady=(4, 0))
        self.sound_label = Muted(parent, font=theme.SOUND, anchor="center")
        self.sound_label.pack()
        SpeakButton(parent, self.speak).pack(pady=(8, 14))

        grid = Box(parent, color=theme.CARD)
        grid.pack(fill="x", padx=40)
        grid.columnconfigure((0, 1), weight=1)
        self.option_buttons = []
        for i in range(self.OPTIONS):
            button = ctk.CTkButton(
                grid,
                text="",
                height=54,
                corner_radius=14,
                font=theme.BODY_BOLD,
                fg_color=theme.CARD_ALT,
                hover_color=theme.ACCENT_SOFT,
                text_color=theme.TEXT,
                border_width=1,
                border_color=theme.BORDER,
                # i=i - "запоминаем" номер кнопки. Без этого все 4 лямбды
                # видели бы последнее значение i (3) - классическая ловушка.
                command=lambda i=i: self.choose(i),
            )
            button.grid(row=i // 2, column=i % 2, sticky="ew", padx=8, pady=6)
            self.option_buttons.append(button)

        self.feedback = ctk.CTkLabel(parent, text="", font=theme.H3, wraplength=700)
        self.feedback.pack(pady=(12, 0))
        self.next_button = GhostButton(parent, "Далее    Enter / Пробел", self.next_word, width=240)
        self.answered = False
        self.options: list[str] = []

    def render(self, word: Word) -> None:
        self.answered = False
        self.en_label.configure(text=word.en)
        self.sound_label.configure(text=f"[ {word.sound} ]")
        self.options = self.vocabulary.distractors(word, self.OPTIONS - 1) + [word.ru]
        random.shuffle(self.options)
        for number, (button, option) in enumerate(zip(self.option_buttons, self.options), start=1):
            button.configure(text=f"{number}.  {option}", fg_color=theme.CARD_ALT, text_color=theme.TEXT, state="normal")
        self.feedback.configure(text="")
        self.next_button.pack_forget()

    def choose(self, index: int) -> None:
        if self.answered:
            return
        self.answered = True
        is_right = self.options[index] == self.word.ru
        self.answer(is_right)
        self._paint_options(chosen=index)
        if is_right:
            self.feedback.configure(text="Right! Верно!", text_color=theme.SUCCESS)
            self.next_later(self.AUTO_NEXT_MS)  # верно - сами переходим дальше
        else:
            text = f"Неверно. Правильно: {self.word.ru}"
            if self.word.example:
                text += f"\n{self.word.example}"
            self.feedback.configure(text=text, text_color=theme.DANGER)
            self.next_button.pack(pady=8)  # ошибка - даём время рассмотреть ответ

    def _paint_options(self, chosen: int) -> None:
        """Верный вариант - зелёным, выбранный неверный - красным, кнопки выключить.

        text_color_disabled - цвет текста у ВЫКЛЮЧЕННОЙ кнопки. По умолчанию
        он серый и плохо читается на зелёном и красном, поэтому задаём сами.
        """
        for i, button in enumerate(self.option_buttons):
            if self.options[i] == self.word.ru:
                button.configure(fg_color=theme.SUCCESS, text_color_disabled=theme.ON_SUCCESS)
            elif i == chosen:
                button.configure(fg_color=theme.DANGER, text_color_disabled=theme.ON_DANGER)
            else:
                button.configure(text_color_disabled=theme.FAINT)
            button.configure(state="disabled")

    def handle_key(self, key: KeyPress) -> bool:
        if key.digit and key.digit <= self.OPTIONS:
            self.choose(key.digit - 1)
        elif key.is_("Return", "space") and self.answered:
            self.next_word()
        else:
            return False
        return True


# =============================================================================
# Написание слова
# =============================================================================


class TypingPage(StudyPage):
    key = "typing"
    title = "Написание слова"
    tagline = "По памяти."
    description = "Напишите английское слово по переводу. Регистр и знаки препинания не важны."

    def build_body(self, parent) -> None:
        Muted(parent, "КАК ПО-АНГЛИЙСКИ", font=theme.LABEL, text_color=theme.FAINT, anchor="center").pack(pady=(16, 0))
        self.ru_label = ctk.CTkLabel(parent, text="", font=theme.WORD_SMALL, text_color=theme.TEXT, wraplength=750)
        self.ru_label.pack(pady=(4, 26))

        row = Box(parent, color=theme.CARD)
        row.pack()
        self.entry = ctk.CTkEntry(
            row,
            width=420,
            height=50,
            corner_radius=12,
            font=theme.H3,
            placeholder_text="введите слово...",
            border_color=theme.LINE_STRONG,
            fg_color=theme.CARD_ALT,
            text_color=theme.TEXT,
        )
        self.entry.pack(side="left")
        # В полях ввода tkinter Ctrl+H по умолчанию стирает символ (как Backspace).
        # Перехватываем: показываем подсказку и возвращаем "break" - это
        # останавливает стандартное действие поля.
        self.entry.bind("<Control-h>", lambda event: (self.show_hint(), "break")[1])
        self.check_button = AccentButton(row, "Проверить", self.submit, width=140, height=50, corner_radius=25)
        self.check_button.pack(side="left", padx=10)

        self.hint_button = GhostButton(parent, "Подсказка    Ctrl+H", self.show_hint, width=200, height=36)
        self.hint_button.pack(pady=14)
        self.feedback = ctk.CTkLabel(parent, text="", font=theme.H3, wraplength=750)
        self.feedback.pack()
        # Кнопка произношения появляется только ПОСЛЕ ответа - иначе она подсказала бы слово.
        self.speak_button = SpeakButton(parent, self.speak)
        Muted(
            parent,
            "ENTER: ПРОВЕРИТЬ  /  ЕЩЁ РАЗ ENTER: ДАЛЬШЕ  /  ПОСЛЕ ОТВЕТА P: ПРОИЗНЕСТИ",
            font=theme.LABEL,
            text_color=theme.FAINT,
            anchor="center",
        ).pack(side="bottom", pady=10)
        self.answered = False

    def render(self, word: Word) -> None:
        self.answered = False
        self.ru_label.configure(text=word.ru)
        self.entry.configure(state="normal")
        self.entry.delete(0, "end")
        self.entry.focus_set()
        self.feedback.configure(text="")
        self.speak_button.pack_forget()
        self.hint_button.configure(state="normal")
        self.check_button.configure(text="Проверить")

    def on_show(self) -> None:
        super().on_show()
        # Вернулись на страницу посреди слова - сразу ставим курсор в поле ввода.
        if self._screen is self.body and not self.answered:
            self.entry.focus_set()

    def speak_text(self) -> str | None:
        # До ответа ничего не произносим: это была бы подсказка.
        return super().speak_text() if self.answered else None

    def show_hint(self) -> None:
        if self.answered:
            return
        hint = AnswerChecker.hint(self.word.answer)
        self.feedback.configure(text=f"{hint}    [ {self.word.sound} ]", text_color=theme.MUTED)
        self.hint_button.configure(state="disabled")

    def submit(self) -> None:
        if self.answered:
            self.next_word()
            return
        typed = self.entry.get()
        if not typed.strip():
            return
        self.answered = True
        is_right = AnswerChecker.is_correct(typed, self.word)
        self.answer(is_right)
        self.entry.configure(state="disabled")
        self.check_button.configure(text="Далее")
        word = f"{self.word.en}   [ {self.word.sound} ]"
        if is_right:
            self.feedback.configure(text=f"Right! {word}", text_color=theme.SUCCESS)
        else:
            self.feedback.configure(text=f"Неверно. Правильно: {word}", text_color=theme.DANGER)
        self.speak_button.pack(pady=(12, 0))
        self.voice.auto_say(self.speak_text())

    def handle_key(self, key: KeyPress) -> bool:
        if key.is_("Return"):
            self.submit()
        elif key.ctrl and key.is_letter("H"):
            self.show_hint()
        else:
            return False
        return True
