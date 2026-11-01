# =============================================================================
# СЛОВАРЬ - поиск слова по-английски или по-русски
# =============================================================================
#
# Результаты выводятся в одно текстовое поле (RichText), а не в сотни
# отдельных меток: так поиск и изменение размера окна работают без задержек.

import customtkinter as ctk

from core.progress import STATUS_NAMES
from gui import theme
from gui.context import AppContext
from gui.hotkeys import KeyPress
from gui.pages.base import Page
from gui.widgets import Muted, RichText


class DictionaryPage(Page):
    key = "dictionary"
    title = "Словарь"
    tagline = "Любое слово."
    description = "Встретили незнакомое слово в книге или документации? Найдите его здесь."
    MAX_RESULTS = 200

    def __init__(self, master, context: AppContext):
        super().__init__(master, context)
        self._after_id = None
        self._speak_tags: list[str] = []  # теги кнопок "Звук" прошлого поиска

        self.build_header()

        self.query = ctk.CTkEntry(
            self,
            height=48,
            font=theme.H3,
            placeholder_text="Поиск: например, commit или кортеж   (Ctrl+F - сюда, Esc - очистить)",
            fg_color=theme.CARD,
            border_color=theme.LINE_STRONG,
            corner_radius=24,
            text_color=theme.TEXT,
        )
        self.query.pack(fill="x", pady=(18, 0))
        # Ищем не на каждое нажатие сразу, а через 200 мс после последнего:
        # пока человек печатает, лишней работы нет.
        self.query.bind("<KeyRelease>", lambda event: self._schedule_search())

        self.info = Muted(self, font=theme.LABEL, text_color=theme.FAINT)
        self.info.pack(anchor="w", pady=(10, 6))

        self.results = RichText(self)
        self.results.pack(fill="both", expand=True)
        box = self.results
        box.define("word", font=(theme.DISPLAY, 18), fg=theme.TEXT, spacing1=12)
        box.define("sound", font=theme.SOUND, fg=theme.ACCENT)
        box.define("ru", font=theme.BODY, fg=theme.TEXT, spacing3=12)
        box.define("topic", font=theme.LABEL, fg=theme.FAINT)
        box.define("link", font=theme.LABEL, fg=theme.ACCENT, underline=True)
        box.define("hint", font=theme.BODY, fg=theme.MUTED, spacing1=12)
        # Статус слова - цветным жирным текстом: красный "Слабое", зелёный "Выучено"...
        for status, color in theme.STATUS_COLORS.items():
            box.define(f"status_{status}", font=theme.LABEL, fg=color)
        # Над ссылкой "Звук" курсор превращается в "руку", как в браузере.
        box.text.tag_bind("link", "<Enter>", lambda event: box.text.configure(cursor="hand2"))
        box.text.tag_bind("link", "<Leave>", lambda event: box.text.configure(cursor="arrow"))

    def on_show(self) -> None:
        self.results.restyle()  # цвета могли поменяться (тёмная/светлая тема)
        self.query.focus_set()
        # Выделяем прошлый запрос: можно сразу печатать новый поверх него.
        self.query.select_range(0, "end")
        self.search()

    def on_key(self, key: KeyPress) -> bool:
        # Esc очищает поиск. Если поле уже пустое - возвращаем False,
        # и окно App обработает Esc как обычно (переход на главную).
        if key.is_("Escape") and self.query.get():
            self.query.delete(0, "end")
            self.search()
            return True
        return False

    def _schedule_search(self) -> None:
        if self._after_id:
            self.after_cancel(self._after_id)
        self._after_id = self.after(200, self.search)

    def search(self) -> None:
        self._after_id = None
        text_widget = self.results.text
        for tag in self._speak_tags:  # убираем привязки кликов от прошлого поиска
            text_widget.tag_delete(tag)
        self._speak_tags.clear()

        text = self.query.get().strip()
        if not text:
            self.info.configure(text=f"В СЛОВАРЕ {len(self.vocabulary)} СЛОВ. НАЧНИТЕ ВВОДИТЬ СЛОВО")
            self.results.write([("Например: loop, commit, refactor, кортеж, переменная.", "hint")])
            return

        found = self.vocabulary.search(text)
        # Сначала точные совпадения, потом начинающиеся с запроса, потом остальные.
        lowered = text.lower()
        found.sort(key=lambda w: (w.answer.lower() != lowered, not w.en.lower().startswith(lowered), len(w.en)))
        shown = found[: self.MAX_RESULTS]

        if not found:
            self.info.configure(text="НИЧЕГО НЕ НАЙДЕНО")
        elif len(found) > len(shown):
            self.info.configure(text=f"НАЙДЕНО {len(found)}, ПОКАЗАНЫ ПЕРВЫЕ {len(shown)}. УТОЧНИТЕ ЗАПРОС")
        else:
            self.info.configure(text=f"НАЙДЕНО: {len(found)}")

        chunks = []
        for index, word in enumerate(shown):
            status = self.progress.status(word)
            speak_tag = f"speak_{index}"  # у каждой ссылки "Звук" свой тег - свой обработчик клика
            self._speak_tags.append(speak_tag)
            chunks += [
                (word.en, "word"),
                (f"   [{word.sound}]   ", "sound"),
                (STATUS_NAMES[status].upper(), f"status_{status}"),
                ("   ", "sound"),
                ("ЗВУК", ("link", speak_tag)),
                ("\n", "word"),
                (word.ru, "ru"),
                (f"    {word.topic.upper()}\n", ("ru", "topic")),
            ]
        self.results.write(chunks or [("Попробуйте другое слово или часть слова.", "hint")])

        for index, word in enumerate(shown):
            # w=word - "запоминаем" слово этой строки (ловушка с lambda в цикле).
            text_widget.tag_bind(f"speak_{index}", "<Button-1>", lambda event, w=word: self.voice.say(w.answer))
