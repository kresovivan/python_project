# =============================================================================
# ГЛАВНОЕ ОКНО - собирает приложение из частей
# =============================================================================
#
# Что это в жизни: "сборщик на конвейере". App при запуске берёт готовые
# детали (словарь, дневник прогресса, настройки, диктора, страницы),
# соединяет их друг с другом и дальше почти ничего не делает сам.
# Такое место в программе называют "точкой сборки" (composition root):
# только здесь решается, какие именно объекты создать.
#
# Каждая часть - в своём файле:
#
#   core/ (логика, без окон)    Vocabulary, Progress, Settings, Speaker, Lesson
#   gui/voice.py                VoiceController - озвучка для интерфейса
#   gui/toast.py                Toast - всплывающие сообщения
#   gui/sidebar.py              Sidebar - боковое меню
#   gui/page_host.py            PageHost - страницы, видна одна
#   gui/help_overlay.py         HelpOverlay - справка по F1
#   gui/pages/*.py              страницы; получают AppContext (gui/context.py)
#
# Сам App отвечает только за: переход между страницами, тему оформления,
# язык обучения, общие горячие клавиши и сохранение состояния при закрытии.
#
# Языков два: английский и китайский (core/language.py). При переключении
# окно разбирает меню и страницы и собирает их заново под новый язык
# (метод _build_language). Прогресс у каждого языка свой.

import tkinter as tk
from pathlib import Path

import customtkinter as ctk

from core.errors_data import ERRORS
from core.language import Language, find_language
from core.progress import Progress
from core.settings import Settings
from core.speech import Speaker
from core.vocabulary import Vocabulary
from gui import theme
from gui.context import AppContext
from gui.help_overlay import HelpOverlay
from gui.hotkeys import KeyPress
from gui.page_host import PageHost
from gui.pages.about import AboutPage
from gui.pages.alphabet import AlphabetPage
from gui.pages.base import Page
from gui.pages.dictionary import DictionaryPage
from gui.pages.errors_page import ErrorsPage
from gui.pages.grammar import GrammarPage, SoundsPage
from gui.pages.home import HomePage
from gui.pages.stats import StatsPage
from gui.pages.study import CardsPage, ChoicePage, TypingPage
from gui.screen import Screens, plan_window
from gui.sidebar import DARK, LIGHT, Sidebar
from gui.toast import Toast
from gui.voice import VoiceController
from gui.widgets import Box

# Порядок классов = порядок пунктов в меню и номера Ctrl+1...9, десятый - Ctrl+0.
# Порядок - путь новичка: азбука, грамматика, потом упражнения со словами.
# Чтобы добавить страницу - создайте класс-наследник Page и допишите его сюда
# (и поправьте "Ctrl + 1-..." в HELP, gui/hotkeys.py: это проверяет тест).
# Больше 10 страниц горячими клавишами не открыть: цифр всего десять.
PAGE_CLASSES: list[type[Page]] = [
    HomePage,
    AlphabetPage,
    GrammarPage,
    CardsPage,
    ChoicePage,
    TypingPage,
    ErrorsPage,
    DictionaryPage,
    StatsPage,
    AboutPage,
]


def page_classes(language: Language) -> list[type[Page]]:
    """Страницы для языка. У китайского вместо азбуки - "Звуки и тоны".

    Ключ у обеих страниц один ("alphabet"), поэтому номер в меню и Ctrl+2
    остаются теми же.
    """
    if not language.sounds:
        return PAGE_CLASSES
    return [SoundsPage if page is AlphabetPage else page for page in PAGE_CLASSES]


class App(ctk.CTk):
    def __init__(self, base_dir: Path, user_data: Path | None = None, speaker: Speaker | None = None):
        """base_dir - где лежат data/ и assets/; user_data - где хранить прогресс.

        Обычно user_data = base_dir/user_data. В exe-версии они разные (см. main.py).

        speaker - "диктор". Обычно не передаётся, и App создаёт настоящий
        Speaker. Тесты окна передают заглушку (tests/gui/base.py, FakeSpeaker):
        она не запускает голос Windows и не ходит в интернет.
        """
        user_data = user_data or base_dir / "user_data"
        # Настройки читаем ДО создания окна - тема оформления нужна сразу.
        self.settings = Settings(user_data / "state.json")
        ctk.set_appearance_mode(self.settings.get("appearance", "dark"))

        # Подгон под монитор (gui/screen.py): выбираем монитор, размер окна и масштаб
        # интерфейса. Масштаб задаём ДО создания виджетов - тогда всё сразу
        # строится нужного размера, без пересчёта.
        Screens.make_dpi_aware()
        # Что запомнили в прошлый раз: {"geometry": "1200x780+150+90", "maximized": False}.
        # (Старые версии хранили только строку "geometry" - подхватываем и её.)
        saved = self.settings.get("window") or {"geometry": self.settings.get("geometry")}
        monitor = Screens.for_start(saved.get("geometry"))
        plan = plan_window(monitor, saved)
        self._normal_geometry = plan.geometry  # размер "не на весь экран" - для сохранения
        ctk.set_widget_scaling(plan.ui_scale)  # размер шрифтов, кнопок, отступов
        ctk.set_window_scaling(plan.ui_scale)  # размер самого окна
        super().__init__(fg_color=theme.BG)

        self.title("English for Programmers")
        icon = base_dir / "assets" / "icon.ico"
        if icon.exists():
            self.iconbitmap(str(icon))  # значок в заголовке окна и на панели задач
        self.geometry(plan.geometry)
        self.minsize(plan.min_width, plan.min_height)
        if plan.maximized:
            # Развернуть после первой отрисовки - иначе Windows запомнит
            # неправильный "обычный" размер окна.
            self.after(50, lambda: self.state("zoomed"))
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # --- общие части: одни на все языки ----------------------------------
        self._base_dir = base_dir
        self._user_data = user_data
        self.toast = Toast(self)
        self.help = HelpOverlay(self)
        language = find_language(self.settings.get("language"))
        language_settings = self._settings_for(language)
        self.speaker = speaker or Speaker(
            user_data / "audio", language_settings.get("voice", language.default_voice)
        )
        self.voice = VoiceController(self, self.speaker, language_settings, self.toast, language)
        self.sidebar: Sidebar | None = None
        self.host: PageHost | None = None
        self.bind("<Key>", self._on_key)  # все нажатия клавиш в окне
        self.protocol("WM_DELETE_WINDOW", self.on_close)  # крестик окна

        # --- части выбранного языка: словарь, прогресс, меню, страницы ---------
        self._build_language(language)
        self._warn_about_damaged_files()

    # --- язык обучения ------------------------------------------------------------

    def _settings_for(self, language: Language) -> Settings:
        """Настройки языка: место остановки, выбранная тема, голос.

        У английского это общий файл user_data/state.json (так было всегда,
        поэтому прогресс старых версий не теряется). У китайского - свой файл
        user_data/zh/state.json. Один и тот же файл не должны писать два
        объекта Settings сразу, поэтому для английского отдаём общий.
        """
        folder = language.user_dir(self._user_data)
        if folder == self._user_data:
            return self.settings
        return Settings(folder / "state.json")

    def _build_language(self, language: Language) -> None:
        """Собрать меню и страницы под язык (при запуске и при переключении)."""
        self.language = language
        self.language_settings = self._settings_for(language)
        self.voice.use(language, self.language_settings)
        # Китайское слово можно найти и по пиньиню: "diannao" находит 电脑.
        sound_key = language.checker.normalize if language.searches_sound else None
        self.vocabulary = Vocabulary.from_folder(language.data_dir(self._base_dir), sound_key)
        self.progress = Progress(language.user_dir(self._user_data) / "progress.json")
        context = AppContext(
            language=language,
            vocabulary=self.vocabulary,
            progress=self.progress,
            settings=self.language_settings,
            errors=ERRORS,
            voice=self.voice,
            navigator=self,  # App выполняет "договор" Navigator: show_page, switch_language
        )
        classes = page_classes(language)
        self.sidebar = Sidebar(
            self,
            pages=[(page.key, page.title) for page in classes],
            voice=self.voice,
            on_navigate=self.show_page,
            on_help=self.toggle_help,
            on_theme=self.change_appearance,
            on_language=self.switch_language,
        )
        self.host = PageHost(self, classes, context)
        # Программа всегда открывается на главной. Незаконченное занятие не теряется:
        # оно показано на главной в блоке "Вы остановились здесь" (Enter - продолжить).
        self.show_page("home")
        # Меню и страницы ставим в окно (grid) только теперь, когда они собраны
        # целиком. Пока виджет не размещён, его не видно, даже если окно
        # перерисуется посреди сборки. Иначе при смене языка на экране
        # мелькали недостроенные куски нового экрана поверх старого.
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self.host.grid(row=0, column=1, sticky="nsew", padx=32, pady=28)

    def switch_language(self, code: str) -> None:
        """Переключить язык обучения: разобрать меню и страницы, собрать заново."""
        language = find_language(code)
        if language is self.language:
            return
        if self.current:
            self.current.on_hide()  # например, остановить анимацию схемы
        self.voice.stop()
        self.settings.set("language", language.code)
        # "Шторка": на время перестройки (около полсекунды) окно закрывает
        # ровный фон с надписью. Под ней старый экран разбирается, а новый
        # собирается, и пользователь не видит промежуточных половинок.
        curtain = Box(self, color=theme.BG)
        ctk.CTkLabel(curtain, text="Переключаю язык...", font=theme.H2, text_color=theme.MUTED).place(
            relx=0.5, rely=0.5, anchor="center"
        )
        curtain.place(relx=0, rely=0, relwidth=1, relheight=1)
        curtain.lift()
        self.update_idletasks()  # нарисовать шторку прямо сейчас
        self.sidebar.destroy()
        self.host.destroy()
        self._build_language(language)
        curtain.destroy()
        self.toast.show(f"Язык: {language.name_ru}. Прогресс у каждого языка свой.", kind=Toast.INFO)

    def toggle_language(self) -> None:
        """Ctrl+L: английский и китайский по очереди."""
        self.switch_language("zh" if self.language.code == "en" else "en")

    def _warn_about_damaged_files(self) -> None:
        """Сказать пользователю, если файл прогресса или настроек был испорчен.

        Сам файл не потерян: JsonStore (core/storage.py) отложил его копию
        рядом под именем вида progress.broken-20261102-011500.json.
        """
        files = (self.progress.backup_path, self.settings.backup_path, self.language_settings.backup_path)
        damaged = list(dict.fromkeys(path.name for path in files if path))
        if damaged:
            self.toast.show(
                f"Файл был повреждён, программа начала с чистого листа. Копия: {', '.join(damaged)}",
                ms=12000,  # 12 секунд: сообщение важное и длинное
            )

    # --- навигация (договор Navigator из gui/context.py) ----------------------

    @property
    def pages(self) -> dict[str, Page]:
        return self.host.pages

    @property
    def current(self) -> Page | None:
        return self.host.current

    def show_page(self, key: str) -> None:
        # Забираем фокус клавиатуры у полей ввода прошлой страницы: иначе
        # цифра, нажатая на новой странице, "напечаталась" бы в скрытое поле.
        self.focus_set()
        previous = self.host.show(key)
        self.sidebar.highlight(previous.key if previous else None, key)

    def page_title(self, key: str) -> str:
        return self.host.title(key)

    # --- тема и справка ---------------------------------------------------------

    def change_appearance(self, value: str) -> None:
        mode = "dark" if value == DARK else "light"
        ctk.set_appearance_mode(mode)
        self.settings.set("appearance", mode)
        if self.current:
            self.current.on_show()  # например, перерисовать график в новых цветах

    def toggle_appearance(self) -> None:
        value = LIGHT if ctk.get_appearance_mode() == "Dark" else DARK
        self.sidebar.show_theme(value)
        self.change_appearance(value)

    def toggle_help(self) -> None:
        self.help.toggle()

    # --- горячие клавиши ----------------------------------------------------------
    # Порядок проверки:
    #   1. открыта справка - работают только F1 и Esc (закрыть);
    #   2. общие сочетания окна (F1, Ctrl+цифра, Ctrl+F, P ...);
    #   3. клавиши текущей страницы (page.on_key);
    #   4. Esc - на главную, если страница не забрала его себе.

    def _on_key(self, event) -> None:
        key = KeyPress.from_event(event)
        if self.help.visible:
            if key.is_("F1", "Escape"):
                self.help.hide()
            return
        if self._on_window_key(key):
            return
        if self.current.on_key(key):
            return
        if key.is_("Escape") and self.current.key != "home":
            self.show_page("home")

    @staticmethod
    def _page_number(digit: int) -> int:
        """Номер пункта меню по цифре: 1-9 как есть, 0 - десятый пункт (как на клавиатуре)."""
        return 10 if digit == 0 else digit

    def _on_window_key(self, key: KeyPress) -> bool:
        """Сочетания, которые работают на любой странице. True - обработано."""
        if key.is_("F1"):
            self.help.show()
        elif key.ctrl and key.digit is not None and self._page_number(key.digit) <= len(self.host.keys):
            self.show_page(self.host.keys[self._page_number(key.digit) - 1])
        elif key.ctrl and key.is_("Tab", "ISO_Left_Tab"):
            self.show_page(self.host.neighbour(-1 if key.shift else 1))
        elif key.ctrl and key.is_letter("F"):
            self.show_page("dictionary")
        elif key.ctrl and key.is_letter("T"):
            self.toggle_appearance()
        elif key.ctrl and key.is_letter("L"):
            self.toggle_language()
        elif key.ctrl and key.is_letter("Q"):
            self.on_close()
        elif not key.ctrl and key.is_letter("P") and not self._typing_in_entry():
            # P - произнести, Shift+P - медленно. В русской раскладке это клавиша "З".
            self.voice.say(self.current.speak_text(), slow=key.shift)
        else:
            return False
        return True

    def _typing_in_entry(self) -> bool:
        """Курсор в АКТИВНОМ поле ввода? Тогда буква P - это просто буква."""
        widget = self.focus_get()
        return isinstance(widget, tk.Entry) and str(widget.cget("state")) != "disabled"

    # --- закрытие -----------------------------------------------------------------

    def on_close(self) -> None:
        # Запоминаем окно. Если оно развёрнуто на весь экран, его "обычный" размер
        # узнать нельзя (geometry() вернёт размер экрана) - оставляем прежний.
        maximized = self.state() == "zoomed"
        geometry = self._normal_geometry if maximized else self.geometry()
        self.settings.set("window", {"geometry": geometry, "maximized": maximized})
        if self.current:
            self.current.on_hide()  # например, остановить анимацию схемы
        # Отменяем отложенные задачи (after), иначе после закрытия они сработают
        # и tkinter напишет в терминал "invalid command name ...".
        # Отменяем именно командой Tcl "after cancel", а НЕ self.after_cancel():
        # after_cancel() заодно удаляет служебную команду, которая принадлежит
        # другому виджету (схеме, озвучке, подсказке). Потом при destroy() тот
        # виджет пытается удалить её второй раз, получает ошибку "can't delete
        # Tcl command" - и окно не закрывается до конца, а программа висит.
        for after_id in self.tk.eval("after info").split():
            self.tk.call("after", "cancel", after_id)
        self.voice.close()  # завершаем фоновый процесс голоса
        self.destroy()
