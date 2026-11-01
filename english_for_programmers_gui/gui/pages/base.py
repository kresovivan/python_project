# =============================================================================
# БАЗОВАЯ СТРАНИЦА - общий родитель всех страниц программы
# =============================================================================
#
# Каждая страница (Главная, Карточки, Словарь, ...) - наследник Page.
# Page задаёт общий "договор": у страницы есть ключ, название в меню
# и методы on_show / on_hide / on_key / speak_text, которые вызывает окно.
# Наследник переопределяет только то, что ему нужно (полиморфизм).
#
# Страница получает AppContext (gui/context.py) - только то, чем ей можно
# пользоваться, а не всё окно целиком.

from core.progress import Progress
from core.settings import Settings
from core.vocabulary import Vocabulary
from gui import theme
from gui.context import AppContext, Navigator
from gui.hotkeys import KeyPress
from gui.voice import VoiceController
from gui.widgets import Box, PageHeader


class Page(Box):
    key = ""  # короткое имя страницы: "home", "cards", ...
    title = ""  # название в боковом меню
    tagline = ""  # вторая часть заголовка, курсивом в цвет акцента: "Слово за словом."
    description = ""  # поясняющий текст под заголовком
    number = 0  # номер в меню: "02 / КАРТОЧКИ". Проставляет PageHost по порядку страниц

    def __init__(self, master, context: AppContext):
        super().__init__(master, color=theme.BG)
        self.context = context

    # Короткие "ярлыки": self.vocabulary вместо self.context.vocabulary.
    # @property - метод, к которому обращаются как к полю.

    @property
    def vocabulary(self) -> Vocabulary:
        return self.context.vocabulary

    @property
    def progress(self) -> Progress:
        return self.context.progress

    @property
    def settings(self) -> Settings:
        return self.context.settings

    @property
    def voice(self) -> VoiceController:
        return self.context.voice

    @property
    def navigator(self) -> Navigator:
        return self.context.navigator

    def build_header(self) -> PageHeader:
        """Шапка страницы: "02 / КАРТОЧКИ", заголовок с курсивом, пояснение."""
        header = PageHeader(self, self.number, f"{self.title}.", self.tagline, self.description)
        header.pack(fill="x")
        return header

    # --- методы, которые переопределяют наследники ------------------------------

    def on_show(self) -> None:
        """Вызывается, когда страницу открыли. Здесь обновляют данные."""

    def on_hide(self) -> None:
        """Вызывается, когда со страницы ушли."""

    def speak_text(self) -> str | None:
        """Английский текст, который произносится по клавише P (None - нечего)."""
        return None

    def on_key(self, key: KeyPress) -> bool:
        """Нажатие клавиши, пока открыта эта страница.

        Вернуть True, если страница обработала клавишу. Тогда окно
        не будет применять к ней своё общее действие (например, Esc).
        """
        return False
