# =============================================================================
# АЗБУКА - английские буквы с картинками, как у первоклассника
# =============================================================================
#
# Что это в жизни: "азбука-книжка". Слева большая буква и картинка, рядом -
# как буква называется, какой звук даёт, слово-пример с переводом. Внизу -
# все 26 букв плитками, как на клавиатуре: щёлкните любую.
#
# Как выбрать букву:
#   стрелки влево и вправо - соседняя буква;
#   клавиша с буквой (в любой раскладке) - сразу эта буква;
#   P - послушать букву и слово (Shift+P - медленно). Поэтому саму букву P
#   открывают стрелками или плиткой: клавиша P занята под "произнести".
#
# Данные (буквы, слова, звуки) - в core/alphabet.py, картинки - assets/alphabet/
# (рисунки OpenMoji, openmoji.org, лицензия CC BY-SA 4.0).

import tkinter as tk
from pathlib import Path

import customtkinter as ctk

from core.alphabet import ALPHABET, Letter, find_letter
from gui import theme
from gui.context import AppContext
from gui.hotkeys import KeyPress
from gui.pages.base import Page
from gui.widgets import Box, Card, Muted, SectionLabel, SpeakButton

PICTURES = Path(__file__).resolve().parents[2] / "assets" / "alphabet"
PICTURE_SOURCE_SIZE = 618  # картинки OpenMoji - 618 x 618 пикселей
PICTURE_SIZE = 190  # какого размера показать картинку (до масштабирования)


class AlphabetPage(Page):
    key = "alphabet"
    title = "Азбука"
    tagline = "Буква за буквой."
    description = "Как называется каждая буква и как она звучит. P - послушать, стрелки или клавиша с буквой - выбрать."

    def __init__(self, master, context: AppContext, number: int = 0):
        super().__init__(master, context, number)
        # Номер буквы запоминается между запусками, как место в "Ошибках Python".
        self.index = self.settings.get("alphabet_index", 0) % len(ALPHABET)
        # tk.PhotoImage нужно где-то хранить: иначе Python удалит картинку из памяти,
        # и на экране останется пустое место. Ключ - имя файла.
        self._pictures: dict[str, tk.PhotoImage] = {}

        self.build_header()
        self._build_letter_card()
        self._build_tiles()

    # --- построение ------------------------------------------------------------

    def _build_letter_card(self) -> None:
        card = Card(self)
        card.pack(fill="both", expand=True, pady=(16, 0))

        # Слева: большая буква и картинка.
        left = Box(card, color=theme.CARD)
        left.pack(side="left", padx=(30, 10), pady=20)
        self.big_letter = ctk.CTkLabel(left, text="", font=(theme.DISPLAY, 120), text_color=theme.ACCENT)
        self.big_letter.pack(side="left")
        # Обычная метка tkinter: CTkLabel умеет показывать только картинки CTkImage,
        # а для них нужна библиотека Pillow, которой нет. Цвет фона - theme.pick().
        self.picture_label = tk.Label(left, bd=0)
        self.picture_label.pack(side="left", padx=(24, 0))

        # Справа: название буквы, звук, слово.
        right = Box(card, color=theme.CARD)
        right.pack(side="left", fill="both", expand=True, padx=(20, 30), pady=24)
        SectionLabel(right, "", "как называется буква").pack(anchor="w")
        self.name_label = ctk.CTkLabel(right, text="", font=theme.H2, text_color=theme.TEXT, anchor="w")
        self.name_label.pack(anchor="w", pady=(0, 12))
        SectionLabel(right, "", "какой звук даёт в словах").pack(anchor="w")
        self.sound_label = Muted(right, font=theme.BODY, wraplength=420)
        self.sound_label.pack(anchor="w", pady=(0, 16))
        SectionLabel(right, "", "слово с этой буквой", color=theme.ACCENT).pack(anchor="w")
        self.word_label = ctk.CTkLabel(right, text="", font=(theme.DISPLAY, 40), text_color=theme.TEXT, anchor="w")
        self.word_label.pack(anchor="w")
        self.translation_label = Muted(right, font=theme.H3, text_color=theme.ACCENT)
        self.translation_label.pack(anchor="w", pady=(0, 14))
        SpeakButton(right, self.speak, text="Послушать (P)").pack(anchor="w")

    def _build_tiles(self) -> None:
        """26 плиток с буквами в два ряда по 13."""
        tiles = Box(self, color=theme.BG)
        tiles.pack(fill="x", pady=(14, 0))
        per_row = 13
        tiles.columnconfigure(tuple(range(per_row)), weight=1, uniform="tiles")
        self.letter_buttons: dict[str, ctk.CTkButton] = {}
        for index, letter in enumerate(ALPHABET):
            button = ctk.CTkButton(
                tiles,
                text=f"{letter.upper}{letter.lower}",
                height=40,
                corner_radius=10,
                font=theme.BODY_BOLD,
                fg_color=theme.CARD,
                hover_color=theme.ACCENT_SOFT,
                text_color=theme.TEXT,
                border_width=1,
                border_color=theme.BORDER,
                # i=index - каждая плитка "помнит" свой номер (ловушка с lambda в цикле).
                command=lambda i=index: self.show(i),
            )
            button.grid(row=index // per_row, column=index % per_row, sticky="ew", padx=3, pady=3)
            self.letter_buttons[letter.upper] = button

    # --- показ буквы -----------------------------------------------------------

    @property
    def letter(self) -> Letter:
        return ALPHABET[self.index]

    def on_show(self) -> None:
        self.render()

    def show(self, index: int) -> None:
        """Открыть букву с этим номером (по кругу: после Z снова A)."""
        self.index = index % len(ALPHABET)
        self.settings.set("alphabet_index", self.index)
        self.render()

    def render(self) -> None:
        letter = self.letter
        self.big_letter.configure(text=f"{letter.upper}{letter.lower}")
        self.picture_label.configure(image=self._picture(letter.picture), bg=theme.pick(theme.CARD))
        self.name_label.configure(text=f"{letter.upper} - [{letter.name_ru}]")
        self.sound_label.configure(text=letter.sound_ru)
        self.word_label.configure(text=f"{letter.word}  [{letter.word_sound}]")
        self.translation_label.configure(text=letter.word_ru)
        for upper, button in self.letter_buttons.items():
            current = upper == letter.upper
            button.configure(
                fg_color=theme.ACCENT if current else theme.CARD,
                text_color=theme.ON_ACCENT if current else theme.TEXT,
            )

    def _picture(self, file_name: str) -> tk.PhotoImage:
        """Картинка нужного размера (с учётом масштаба экрана), загруженная один раз.

        subsample(n) уменьшает картинку в n раз (только в целое число раз):
        618 пикселей при масштабе 200% дают 309, при 100% - 206.
        """
        if file_name not in self._pictures:
            scale = ctk.ScalingTracker.get_widget_scaling(self)
            step = max(1, round(PICTURE_SOURCE_SIZE / (PICTURE_SIZE * scale)))
            self._pictures[file_name] = tk.PhotoImage(file=str(PICTURES / file_name)).subsample(step)
        return self._pictures[file_name]

    # --- клавиши и звук ------------------------------------------------------------

    def on_key(self, key: KeyPress) -> bool:
        if key.is_("Right"):
            self.show(self.index + 1)
        elif key.is_("Left"):
            self.show(self.index - 1)
        elif not key.ctrl and ord("A") <= key.code <= ord("Z"):
            # Номер физической клавиши совпадает с кодом латинской буквы (F = 70):
            # так буква находится и в русской раскладке.
            self.show(ALPHABET.index(find_letter(chr(key.code))))
        else:
            return False
        return True

    def speak_text(self) -> str | None:
        return self.letter.speech

    def speak(self) -> None:
        self.voice.say(self.speak_text())
