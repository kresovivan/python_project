# -*- coding: utf-8 -*-
"""Приложение питомца: связывает атлас, окно, репетитора и озвучку.

Что это в жизни: "дрессировщик". Атлас даёт кадры, окно ловит мышку,
репетитор даёт слова, диктор их произносит - а KisunchikApp решает,
что из этого показать прямо сейчас, и крутит главный цикл анимации.
"""

import ctypes
import time
from ctypes import wintypes
from pathlib import Path

from PIL import Image

from core import autostart
from core.atlas import SpriteAtlas
from core.behavior import BehaviorPolicy
from core.bubble import BubbleImage
from core.progress import ProgressStore
from core.settings import Settings
from core.speech import Speaker
from core.tutor import EnglishTutor
from gui.renderer import LayeredRenderer
from gui.screen import VirtualScreen
from gui.window import PetWindow

TICK_MS = 30          # перерисовка кадра
CARD_SECONDS = 9.0    # сколько висит карточка со словом
BUBBLE_WIDTH = 470    # минимальная ширина пузыря (дальше он растёт под текст)
BUBBLE_GAP = 12       # отступ пузыря от края окна

# Цвета меню: сливки и карамель под рыжего котика.
MENU_STYLE = dict(
    bg="#FFF9F1", fg="#4A3226",
    activebackground="#F0913C", activeforeground="#FFFFFF",
    disabledforeground="#B8A99B", selectcolor="#E87E2B",
    font=("Segoe UI", 10),
)


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]


def system_idle_seconds() -> float:
    """Сколько секунд пользователь не трогал мышку и клавиатуру."""
    info = LASTINPUTINFO()
    info.cbSize = ctypes.sizeof(LASTINPUTINFO)
    if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info)):
        return 0.0
    # GetTickCount без restype обрезается до знакового c_int: после
    # ~25 дней аптайма число стало бы отрицательным, и idle ломается.
    k32 = ctypes.windll.kernel32
    k32.GetTickCount.restype = wintypes.DWORD
    return (k32.GetTickCount() - info.dwTime) / 1000.0


class KisunchikApp:
    """Настольный питомец: анимация, трюки, прогулки, английские слова."""

    def __init__(self, assets_dir: Path, scale: float = 0.5, log_path: Path | None = None,
                 clock=None, idle_probe=None, settings: Settings | None = None,
                 settings_path: Path | None = None, autostart_sync=None,
                 autostart_check=None, progress_path: Path | None = None):
        # clock и idle_probe подменяются в тестах: так проверяем поведение
        # за "часы" виртуального времени, не ожидая их по-настоящему.
        # autostart_sync в тестах подменяется заглушкой, чтобы тесты
        # не трогали настоящий реестр.
        self._clock = clock or time.monotonic
        self._idle_probe = idle_probe or system_idle_seconds
        self._autostart_sync = autostart_sync or autostart.apply
        if autostart_check is not None:
            self._autostart_check = autostart_check
        elif autostart_sync is not None:
            # В тестах реестр не читаем: считаем, что всё получилось.
            self._autostart_check = lambda: self.settings.autostart
        else:
            self._autostart_check = autostart.is_enabled
        self._log_path = log_path
        self.settings = settings or Settings()
        self._settings_path = settings_path
        self._assets_dir = assets_dir
        scale = self.settings.scale  # настройка важнее параметра
        self.atlas = SpriteAtlas(assets_dir / "pet.json", assets_dir / "spritesheet.png", scale)
        # Дневник обучения: помнит, на каком слове остановились,
        # даже если выключили котика или компьютер.
        self.progress = ProgressStore(progress_path) if progress_path else None
        self.tutor = EnglishTutor(assets_dir / "words.json",
                                  assets_dir / "categories.json",
                                  progress=self.progress)
        self.speaker = Speaker()
        self.policy = BehaviorPolicy()
        self.screen = VirtualScreen()
        self.renderer = LayeredRenderer(log=self._log)
        self.window = PetWindow(self.screen, self.renderer,
                                (self.atlas.out_width, self.atlas.out_height))
        self.window.on_zone = self._on_zone
        self.window.on_double = lambda: self._play_once("celebrate")
        self.window.on_exit = self._exit
        # Перед показом меню перестраиваем его: подписи блоков несут
        # свежие цифры прогресса.
        self.window.on_menu = self._build_menu
        self._build_menu()
        self.apply_settings()

        self.bubble_maker = BubbleImage(min_width=BUBBLE_WIDTH, max_width=780)

        # Текущее состояние анимации.
        self.state = "idle"
        self.frame = 0
        self.last_frame_at = self._clock()
        self.one_shot: str | None = None
        self.walk_target: int | None = None

        # Расписание самодеятельности.
        now = self._clock()
        self.next_fun_at = now + self.policy.next_fun_delay()
        self.next_walk_at = now + self.policy.next_walk_delay()
        self.next_word_at = now + self.policy.next_word_delay()

        # Карточка со словом.
        self._card_until = 0.0
        self._card_word = None
        self._card_image = None

        # Сон: котик засыпает, когда пользователь долго ничего не делает,
        # и просыпается от клика.
        self.sleeping = False

        # Подпись последнего нарисованного кадра - чтобы не рисовать
        # одно и то же по кругу (экономия процессора).
        self._last_push_signature = None

        self._running = False

    # --- журнал ---

    def _log(self, message: str) -> None:
        if not self._log_path:
            return
        try:
            with open(self._log_path, "a", encoding="utf-8") as f:
                f.write(time.strftime("%H:%M:%S ") + message + "\n")
        except OSError:
            pass

    # --- настройки ---

    def apply_settings(self, notify: bool = False) -> None:
        """Применить текущие настройки к поведению котика.

        notify=True - если что-то не получилось (антивирус запретил
        автозапуск), показать пузырь с пояснением. При старте программы
        пузырь не показываем, только журнал: человек ещё ничего не нажимал.
        """
        s = self.settings
        # Голос и блоки слов применяются к диктору и репетитору.
        self.speaker.set_voice(s.voice)
        self.tutor.set_categories(set(s.categories) if s.categories is not None else None)
        self.policy.sleep_after_idle = s.sleep_after_idle
        self.policy.fun_period = (s.fun_every * 0.6, s.fun_every * 1.4)
        self.policy.walk_delay = (s.walk_every * 0.6, s.walk_every * 1.4)
        self.policy.word_period = (s.word_every * 0.7, s.word_every * 1.3)
        # Автозапуск: сначала читаем факт, и только если он расходится
        # с настройкой - пишем. Лишних записей быть не должно: антивирус
        # реагирует на саму попытку записи и откатывает даже чужие
        # (рабочие) записи автозапуска.
        try:
            actual = self._autostart_check()
        except OSError:
            actual = s.autostart  # не прочитали - не трогаем
        if actual != s.autostart:
            try:
                self._autostart_sync(s.autostart)
            except OSError as exc:
                self._log(f"автозапуск не настроился: {exc}")
            # Проверяем факт: антивирус может молча запретить запись.
            # Галочка в меню не должна врать - откатываем настройку.
            try:
                actual = self._autostart_check()
            except OSError:
                actual = s.autostart
        if actual != s.autostart:
            self._log(f"автозапуск: просили {s.autostart}, по факту {actual} "
                      f"(вероятно, антивирус запретил)")
            s.autostart = actual
            if self._settings_path:
                from core.settings import save
                save(self._settings_path, s)
            if hasattr(self.window, "autostart_var"):
                self.window.autostart_var.set(actual)
            if notify and hasattr(self, "bubble_maker"):
                wanted = "включить" if not actual else "выключить"
                self.show_message(
                    "Кисунчик",
                    f"Антивирус не дал мне {wanted} автозапуск, галочку "
                    f"вернул как было. Разрешите KisunchikPet.exe "
                    f"в антивирусе или поменяйте запись вручную.")
        # Размер котика: пересобираем кадры в новом масштабе.
        if abs(self.atlas.out_width - int(self.atlas.frame_width * s.scale)) > 1:
            self.atlas = SpriteAtlas(self._assets_dir / "pet.json",
                                     self._assets_dir / "spritesheet.png", s.scale)
            self.window.cat_w = self.atlas.out_width
            self.window.cat_h = self.atlas.out_height
            self.window.win_w = self.atlas.out_width
            self.window.win_h = self.atlas.out_height

    def change_settings(self, **kwargs) -> None:
        """Поменять настройки из меню, сохранить и применить."""
        for key, value in kwargs.items():
            setattr(self.settings, key, value)
        if self._settings_path:
            from core.settings import save
            save(self._settings_path, self.settings)
        self.apply_settings(notify=True)
        self._log(f"настройки: {kwargs}")

    def _build_menu(self) -> None:
        """Меню по правому клику: все настройки, которые имеет смысл
        менять пользователю.

        Перестраивается при каждом открытии (см. on_menu в PetWindow):
        подписи блоков слов показывают свежий прогресс "пройдено/всего".
        """
        import tkinter as tk
        m = self.window.menu
        s = self.settings
        m.delete(0, "end")
        m.config(**MENU_STYLE)

        def sub(parent) -> tk.Menu:
            """Подменю в общем стиле: сливки и карамель."""
            return tk.Menu(parent, tearoff=0, **MENU_STYLE)

        m.add_command(label="Кисунчик - о программе",
                      command=self.show_about)
        m.add_separator()

        # Настроек много - раскладываем их по трём группам, чтобы
        # меню не превращалось в простыню.
        look_menu = sub(m)    # как котик выглядит и двигается
        learn_menu = sub(m)   # чему и как учит
        sound_menu = sub(m)   # голос и звук

        size_menu = sub(look_menu)
        for label, val in [("Мелкий", 0.5), ("Средний", 0.75), ("Крупный", 1.0)]:
            size_menu.add_radiobutton(
                label=label, value=val,
                variable=self.window.size_var,
                command=lambda v=val: self.change_settings(scale=v))
        look_menu.add_cascade(label="Размер котика", menu=size_menu)
        self.window.size_var.set(s.scale)

        sleep_menu = sub(look_menu)
        for label, val in [("1 минуту", 60), ("3 минуты", 180),
                           ("5 минут", 300), ("10 минут", 600)]:
            sleep_menu.add_radiobutton(
                label=label, value=val,
                variable=self.window.sleep_var,
                command=lambda v=val: self.change_settings(sleep_after_idle=v))
        look_menu.add_cascade(label="Засыпает после тишины", menu=sleep_menu)
        self.window.sleep_var.set(s.sleep_after_idle)

        fun_menu = sub(look_menu)
        for label, val in [("Редко", 90), ("Обычно", 40), ("Часто", 20)]:
            fun_menu.add_radiobutton(
                label=label, value=val,
                variable=self.window.fun_var,
                command=lambda v=val: self.change_settings(fun_every=v))
        look_menu.add_cascade(label="Затеи (рыбка, лапка...)", menu=fun_menu)
        self.window.fun_var.set(s.fun_every)

        walk_menu = sub(look_menu)
        for label, val in [("Редко", 120), ("Обычно", 55), ("Часто", 30)]:
            walk_menu.add_radiobutton(
                label=label, value=val,
                variable=self.window.walk_var,
                command=lambda v=val: self.change_settings(walk_every=v))
        look_menu.add_cascade(label="Прогулки по экрану", menu=walk_menu)
        self.window.walk_var.set(s.walk_every)

        look_menu.add_checkbutton(
            label="Гуляет по экрану сам",
            variable=self.window.walking_var,
            command=lambda: self.change_settings(
                walking=bool(self.window.walking_var.get())))
        self.window.walking_var.set(s.walking)

        word_menu = sub(learn_menu)
        for label, val in [("Каждые 3 мин", 180), ("Каждые 7 мин", 420),
                           ("Каждые 15 мин", 900)]:
            word_menu.add_radiobutton(
                label=label, value=val,
                variable=self.window.word_var,
                command=lambda v=val: self.change_settings(word_every=v))
        learn_menu.add_cascade(label="Автопоказ слов", menu=word_menu)
        self.window.word_var.set(s.word_every)

        learn_menu.add_checkbutton(
            label="Сам показывает слова",
            variable=self.window.auto_words_var,
            command=lambda: self.change_settings(
                auto_words=bool(self.window.auto_words_var.get())))
        self.window.auto_words_var.set(s.auto_words)

        # Блоки слов: пользователь выбирает, из каких тем учить.
        # Галочек много - кладём их в каскад по группам (темы, части речи...).
        groups = self.tutor.category_groups()
        if groups:
            words_menu = sub(learn_menu)
            group_titles = {"basics": "Азбука и основы", "topics": "Темы",
                            "speech": "Части речи", "style": "Фразы и стиль"}
            enabled = set(s.categories) if s.categories is not None else None
            for group_key, cats in groups.items():
                sub_menu = sub(words_menu)
                for cat in cats:
                    # Переменные галочек: не создаём новые, а переиспользуем
                    # (иначе старые Tcl-переменные остаются висеть — утечка).
                    var = self.window.cat_vars.get(cat["id"])
                    if var is None:
                        var = tk.IntVar()
                        self.window.cat_vars[cat["id"]] = var
                    var.set(1 if enabled is None or cat["id"] in enabled else 0)
                    # Подпись с прогрессом: видно, где продолжить,
                    # а где начать с нуля. "не начата" - для нуля.
                    done, total = self.tutor.category_status(cat["id"])
                    note = f"{done}/{total}" if done else f"не начата, {total}"
                    sub_menu.add_checkbutton(
                        label=f'{cat["title"]}  ({note})', variable=var,
                        command=self._apply_category_choice)
                words_menu.add_cascade(
                    label=group_titles.get(group_key, group_key), menu=sub_menu)
            learn_menu.add_cascade(label="Что учить", menu=words_menu)

        # Табло прогресса: графики по блокам и дням недели.
        if self.progress is not None:
            learn_menu.add_command(label="Прогресс обучения...",
                                   command=self.show_progress)

        sound_menu.add_checkbutton(
            label="Озвучка слов голосом",
            variable=self.window.sound_var,
            command=lambda: self.change_settings(
                sound=bool(self.window.sound_var.get())))
        self.window.sound_var.set(s.sound)

        # Голос озвучки: офлайн-персонажи Windows и онлайн-голоса Google.
        from core.speech import voice_choices
        voice_menu = sub(sound_menu)
        for spec, label in voice_choices():
            voice_menu.add_radiobutton(
                label=label, value=spec,
                variable=self.window.voice_var,
                command=lambda v=spec: self.change_settings(voice=v))
        sound_menu.add_cascade(label="Голос озвучки", menu=voice_menu)
        self.window.voice_var.set(s.voice)

        m.add_cascade(label="Вид и поведение", menu=look_menu)
        m.add_cascade(label="Обучение", menu=learn_menu)
        m.add_cascade(label="Озвучка", menu=sound_menu)

        m.add_separator()
        m.add_checkbutton(
            label="Запускать вместе с Windows",
            variable=self.window.autostart_var,
            command=lambda: self.change_settings(
                autostart=bool(self.window.autostart_var.get())))
        self.window.autostart_var.set(s.autostart)

        m.add_separator()
        m.add_command(label="Выход", command=self._exit)

    def _apply_category_choice(self) -> None:
        """Собрать отмеченные блоки и сохранить в настройки.

        Если отмечены все блоки - храним None ("все"), так настройка
        переживёт появление новых блоков в словаре.
        """
        all_ids = list(self.window.cat_vars)
        enabled = sorted(cat_id for cat_id in all_ids
                         if self.window.cat_vars[cat_id].get())
        self.change_settings(
            categories=None if len(enabled) == len(all_ids) else enabled)

    # --- карточка со словом ---

    def show_word(self, word=None) -> None:
        """Показать пузырь со словом рядом с котиком."""
        if word is None:
            word = self.tutor.next_word()  # само отметится в дневнике
            if word is None:               # словарь пуст или все блоки выключены
                return
        elif self.progress is not None:
            # Слово задано извне (например, последнее из прошлого сеанса).
            self.progress.mark_shown(word.en)
        self._card_word = word
        if self.progress is not None:
            self.progress.save()  # пишет только при изменениях
        # В подзаголовке - транскрипция и название блока: видно,
        # из какой темы слово.
        cat_title = self.tutor.category_title(word.category)
        subtitle = f"{word.transcription} · {cat_title}" if cat_title \
            else word.transcription
        self._card_image = self.bubble_maker.render(
            title=word.en,
            subtitle=subtitle,
            lines_text=word.ru,
            tail="bottom-right",
        )
        self._card_until = self._clock() + CARD_SECONDS
        # Расширяем окно под пузырь: влево на ширину пузыря, вверх на высоту.
        bw, bh = self._card_image.size
        if self.window.win_w == self.window.cat_w:
            self.window.resize_for_bubble(bw + BUBBLE_GAP, max(0, bh - self.window.cat_h + BUBBLE_GAP))

    def show_message(self, title: str, text: str) -> None:
        """Показать пузырь со свободным текстом: предупреждения, подсказки.

        Словарной карточки при этом нет - клик по животику покажет
        обычное слово, как будто пузыря и не было.
        """
        self._card_word = None
        self._card_image = self.bubble_maker.render(
            title=title, subtitle="", lines_text=text, tail="bottom-right")
        self._card_until = self._clock() + CARD_SECONDS
        bw, bh = self._card_image.size
        if self.window.win_w == self.window.cat_w:
            self.window.resize_for_bubble(bw + BUBBLE_GAP, max(0, bh - self.window.cat_h + BUBBLE_GAP))

    def show_about(self) -> None:
        """Открыть визитку программы (одно окно на приложение)."""
        from gui.about_window import AboutWindow
        win = getattr(self, "_about_window", None)
        if win is not None and win.is_alive():
            win.win.lift()
            return
        self._about_window = AboutWindow(self.window.root)

    def show_progress(self) -> None:
        """Открыть табло прогресса обучения (одно окно на приложение)."""
        from gui.progress_window import ProgressWindow
        win = getattr(self, "_progress_window", None)
        if win is not None and win.is_alive():
            win.refresh()
            win.win.lift()
            return
        self._progress_window = ProgressWindow(self.window.root, self.tutor,
                                               self.progress)

    def hide_word(self) -> None:
        """Убрать пузырь и вернуть окно к размеру котика."""
        self._card_word = None
        self._card_image = None
        self._card_until = 0.0
        if self.window.win_w != self.window.cat_w:
            self.window.resize_cat_only()

    # --- реакции на мышь ---

    def _on_zone(self, zone: str) -> None:
        # Любой клик будит спящего котика - и сразу выполняет действие
        # зоны: человек кликнул с намерением, обижать его не надо.
        self._log(f"клик: {zone}, спал={self.sleeping}")
        if self.sleeping:
            self.sleeping = False
            self.state = "idle"
            self.frame = 0
        if zone == "head":
            # Голова: новое слово с переводом.
            self.show_word()
            self._play_once("paw_wave")
        elif zone == "belly":
            # Животик: произнести слово по-английски. Если карточки нет -
            # сначала показать её, чтобы было видно, что звучит.
            if self._card_word is None:
                self.show_word()
            if self.settings.sound:
                said = self.speaker.say(self._card_word.en)
                if said and self.progress is not None:
                    self.progress.mark_said(self._card_word.en)
                    self.progress.save()
                if not said:
                    # Диктор мог не успеть запуститься или умереть -
                    # пробуем поднять его заново.
                    self._log(f"озвучка не сработала: {self.speaker.error}, перезапуск")
                    self.speaker.restart()
                else:
                    # SAID прилетит через секунду-две: диктор подтверждает
                    # каждую произнесённую фразу, счётчик растёт.
                    self._log(f"сказал диктору '{self._card_word.en}', "
                              f"подтверждено фраз: {self.speaker.said_count}, "
                              f"ошибка синтеза: {self.speaker.speech_error}")
            self._card_until = self._clock() + CARD_SECONDS
            self._play_once("somersault")
        elif zone == "tail":
            self.hide_word()
            self._play_once("annoyed")

    # --- анимация ---

    def _play_once(self, name: str) -> None:
        """Сыграть разовое движение и вернуться в idle."""
        if name not in self.atlas.state_names():
            return
        self.one_shot = name
        self.state = name
        self.frame = 0
        self.last_frame_at = self._clock()

    def _amuse_self(self, now: float) -> None:
        """Самодеятельность: гуляем, балуемся, учим слова, спим.

        Затеи и прогулки НЕ ждут, пока пользователь отойдёт от компьютера -
        иначе котик выглядит мёртвым как раз тогда, когда на него смотрят.
        От бездействия зависит только сон и автопоказ слов.
        """
        if self.one_shot or self.walk_target is not None:
            return
        idle_for = self._idle_probe()
        if self.sleeping:
            # Спим, пока пользователь не вернулся.
            if idle_for < 2:
                self.sleeping = False
                self.state = "idle"
                self.frame = 0
                self._log("проснулся")
            return
        if idle_for > self.policy.sleep_after_idle:
            # Сначала дремлем (doze_off), потом крепко спим (sleeping).
            self.sleeping = True
            self.state = "doze_off"
            self.frame = 0
            self.last_frame_at = now
            self.hide_word()
            self._log("заснул")
            return
        if now >= self.next_walk_at and self.settings.walking:
            # Гуляем только по тому монитору, где котик сейчас сидит.
            # Иначе он убегает в "пустоту": у соседнего монитора может
            # быть другая высота, и там, где ходит котик, экрана нет.
            cat_offset = self.window.win_w - self.window.cat_w
            cat_x = self.window.pos_x + cat_offset
            cat_y = self.window.pos_y + (self.window.win_h - self.window.cat_h)
            area = self.screen.area_at(cat_x + self.window.cat_w // 2,
                                       cat_y + self.window.cat_h // 2)
            target = self.policy.walk_target(
                cat_x, area.left, area.right - self.window.cat_w)
            delta = target - cat_x
            if delta:
                # Цель храним в координатах КОТИКА, а не окна: иначе
                # появление пузыря (окно шире, сдвиг влево) уводило
                # котика за правый край экрана.
                self.walk_target = target
                self.state = "running_left" if delta < 0 else "running_right"
                self.frame = 0
                self._log(f"пошёл гулять: {self.state}, цель {self.walk_target}, "
                          f"монитор {area}")
            self.next_walk_at = now + self.policy.next_walk_delay()
            return
        if now >= self.next_word_at and idle_for > 20 and self.settings.auto_words:
            # Раз в несколько минут сам показывает карточку со словом.
            self.show_word()
            self.next_word_at = now + self.policy.next_word_delay()
            self._log(f"показал слово {self._card_word.en}")
            return
        if now >= self.next_fun_at:
            name = self._rng_choice(
                ["idle_random_1", "idle_random_2", "paw_wave", "fish_snack"])
            self._play_once(name)
            self.next_fun_at = now + self.policy.next_fun_delay()
            self._log(f"затеял: {name}")

    def _rng_choice(self, items):
        import random
        return random.choice(items)

    def _advance_frame(self, now: float) -> None:
        """Переключить кадры анимации по расписанию."""
        st = self.atlas.info(self.state)
        interval = 1.0 / st.fps
        if now - self.last_frame_at < interval:
            return
        steps = max(1, int((now - self.last_frame_at) / interval))
        self.last_frame_at += steps * interval

        if self.walk_target is not None:
            # Идём к цели: 3 пикселя на кадр. Цель - в координатах
            # котика; окно может быть шире котика (пузырь слева).
            cat_offset = self.window.win_w - self.window.cat_w
            cat_x = self.window.pos_x + cat_offset
            direction = 1 if self.walk_target > cat_x else -1
            cat_x += direction * 3 * steps
            done = (direction > 0 and cat_x >= self.walk_target) or \
                   (direction < 0 and cat_x <= self.walk_target)
            if done:
                cat_x = self.walk_target
                self.walk_target = None
                self.state = "idle"
                self.frame = 0
            self.window.pos_x = cat_x - cat_offset
        if self.one_shot:
            self.frame += steps
            if self.frame >= self.atlas.info(self.state).frames:
                self.one_shot = None
                self.state = "idle"
                self.frame = 0
        elif self.sleeping and self.state == "doze_off":
            # Додремали до конца ряда - переходим в крепкий сон.
            self.frame += steps
            if self.frame >= self.atlas.info("doze_off").frames:
                self.state = "sleeping"
                self.frame = 0
        else:
            self.frame = (self.frame + steps) % self.atlas.info(self.state).frames

    def _keep_on_screen(self) -> None:
        """Страховка: котик всегда целиком на каком-то мониторе.

        Срабатывает в каждом кадре и ловит все пути, которыми котик
        мог уползти за край: гонка прогулки и пузыря, перетаскивание
        на стык мониторов разной высоты, смена масштаба. Сначала окно
        поджимается к виртуальному экрану целиком, потом сам котик -
        к своему монитору; котик важнее пузыря.
        """
        w = self.window
        # Окно целиком - внутри виртуального экрана.
        nx, ny = self.screen.all.clamp(w.pos_x, w.pos_y, w.win_w, w.win_h)
        if (nx, ny) != (w.pos_x, w.pos_y):
            w.pos_x, w.pos_y = nx, ny
        # Котик целиком - внутри своего монитора.
        cat_off_x = w.win_w - w.cat_w
        cat_off_y = w.win_h - w.cat_h
        cat_x = w.pos_x + cat_off_x
        cat_y = w.pos_y + cat_off_y
        area = self.screen.area_at(cat_x + w.cat_w // 2, cat_y + w.cat_h // 2)
        nx, ny = area.clamp(cat_x, cat_y, w.cat_w, w.cat_h)
        if (nx, ny) != (cat_x, cat_y):
            w.pos_x = nx - cat_off_x
            w.pos_y = ny - cat_off_y
            if self.walk_target is not None:
                # Цель стала недостижимой - прекращаем прогулку.
                self.walk_target = None
                if self.state in ("running_left", "running_right"):
                    self.state = "idle"
                    self.frame = 0

    def _compose(self, cat_frame) -> Image.Image:
        """Собрать картинку окна: пузырь слева сверху, котик в углу."""
        if self._card_image is None:
            return cat_frame
        canvas = Image.new("RGBA", (self.window.win_w, self.window.win_h), (0, 0, 0, 0))
        canvas.paste(self._card_image, (BUBBLE_GAP // 2, 0), self._card_image)
        off_x, off_y = self.window.cat_offset()
        canvas.paste(cat_frame, (off_x, off_y), cat_frame)
        return canvas

    def tick(self) -> None:
        """Один шаг главного цикла."""
        now = self._clock()
        self._amuse_self(now)
        self._advance_frame(now)
        self._keep_on_screen()
        if self._card_image is not None and now >= self._card_until:
            self.hide_word()
        # Перерисовываем окно, только если что-то реально изменилось:
        # кадр, позиция или пузырь. Без этого котик 33 раза в секунду
        # гонял один и тот же кадр через numpy в Windows - лишние
        # 8-9% процессора за невидимую работу.
        signature = (self.state, self.frame,
                     self.window.pos_x, self.window.pos_y,
                     self.window.win_w, self.window.win_h,
                     id(self._card_image))
        if signature != self._last_push_signature:
            self._last_push_signature = signature
            cat_frame = self.atlas.frames(self.state)[self.frame]
            self.renderer.push(self.window.hwnd, self._compose(cat_frame),
                               self.window.pos_x, self.window.pos_y)
        if self._running:
            self.window.root.after(TICK_MS, self._tick_safe)

    def _tick_safe(self) -> None:
        """Один шаг цикла с защитой: ошибка в кадре не должна
        убивать всю анимацию - пишем в журнал и живём дальше."""
        try:
            self.tick()
        except Exception:
            import traceback
            self._log(traceback.format_exc())
            if self._running:
                self.window.root.after(TICK_MS, self._tick_safe)

    def _exit(self) -> None:
        self._running = False
        if self.progress is not None:
            self.progress.save(force=True)  # дневник - на диск перед сном
        self.speaker.close()
        self.window.root.destroy()

    def run(self) -> None:
        self._running = True
        self._log(f"старт, hwnd={self.window.hwnd}, "
                  f"позиция={self.window.pos_x},{self.window.pos_y}, "
                  f"экраны: {self.screen.all}")
        self.tick()
        # Диктор поднимается в фоне - запишем в журнал, как он себя чувствует.
        from core.speech import ENGINE
        self.window.root.after(2000, lambda: self._log(
            f"диктор: готов={self.speaker.ready}, голос={self.speaker.voice}, "
            f"движок={ENGINE}, ошибка={self.speaker.error}"))
        self.window.root.mainloop()
