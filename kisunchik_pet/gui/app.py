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

from core.atlas import SpriteAtlas
from core.behavior import BehaviorPolicy
from core.bubble import BubbleImage
from core.speech import Speaker
from core.tutor import EnglishTutor
from gui.renderer import LayeredRenderer
from gui.screen import VirtualScreen
from gui.window import PetWindow

TICK_MS = 30          # перерисовка кадра
CARD_SECONDS = 9.0    # сколько висит карточка со словом
BUBBLE_WIDTH = 340    # ширина пузыря
BUBBLE_GAP = 10       # отступ пузыря от края окна


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]


def system_idle_seconds() -> float:
    """Сколько секунд пользователь не трогал мышку и клавиатуру."""
    info = LASTINPUTINFO()
    info.cbSize = ctypes.sizeof(LASTINPUTINFO)
    if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info)):
        return 0.0
    return (ctypes.windll.kernel32.GetTickCount() - info.dwTime) / 1000.0


class KisunchikApp:
    """Настольный питомец: анимация, трюки, прогулки, английские слова."""

    def __init__(self, assets_dir: Path, scale: float = 0.5, log_path: Path | None = None):
        self._log_path = log_path
        self.atlas = SpriteAtlas(assets_dir / "pet.json", assets_dir / "spritesheet.png", scale)
        self.tutor = EnglishTutor(assets_dir / "words.json")
        self.speaker = Speaker()
        self.policy = BehaviorPolicy()
        self.screen = VirtualScreen()
        self.renderer = LayeredRenderer(log=self._log)
        self.window = PetWindow(self.screen, self.renderer,
                                (self.atlas.out_width, self.atlas.out_height))
        self.window.on_zone = self._on_zone
        self.window.on_double = lambda: self._play_once("celebrate")
        self.window.on_exit = self._exit

        self.bubble_maker = BubbleImage(width=BUBBLE_WIDTH)

        # Текущее состояние анимации.
        self.state = "idle"
        self.frame = 0
        self.last_frame_at = time.monotonic()
        self.one_shot: str | None = None
        self.walk_target: int | None = None

        # Расписание самодеятельности.
        now = time.monotonic()
        self.next_fun_at = now + self.policy.next_fun_delay()
        self.next_walk_at = now + self.policy.next_walk_delay()
        self.next_word_at = now + self.policy.next_word_delay()

        # Карточка со словом.
        self._card_until = 0.0
        self._card_word = None
        self._card_image = None

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

    # --- карточка со словом ---

    def show_word(self, word=None) -> None:
        """Показать пузырь со словом рядом с котиком."""
        word = word or self.tutor.next_word()
        self._card_word = word
        self._card_image = self.bubble_maker.render(
            title=word.en,
            subtitle=word.transcription,
            lines_text=word.ru,
            tail="bottom-right",
        )
        self._card_until = time.monotonic() + CARD_SECONDS
        # Расширяем окно под пузырь: влево на ширину пузыря, вверх на высоту.
        bw, bh = self._card_image.size
        if self.window.win_w == self.window.cat_w:
            self.window.resize_for_bubble(bw + BUBBLE_GAP, max(0, bh - self.window.cat_h + BUBBLE_GAP))

    def hide_word(self) -> None:
        """Убрать пузырь и вернуть окно к размеру котика."""
        self._card_word = None
        self._card_image = None
        self._card_until = 0.0
        if self.window.win_w != self.window.cat_w:
            self.window.resize_cat_only()

    # --- реакции на мышь ---

    def _on_zone(self, zone: str) -> None:
        if zone == "head":
            # Голова: новое слово с переводом.
            self.show_word()
            self._play_once("paw_wave")
        elif zone == "belly":
            # Животик: произнести слово по-английски. Если карточки нет -
            # сначала показать её, чтобы было видно, что звучит.
            if self._card_word is None:
                self.show_word()
            self.speaker.say(self._card_word.en)
            self._card_until = time.monotonic() + CARD_SECONDS
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
        self.last_frame_at = time.monotonic()

    def _amuse_self(self, now: float) -> None:
        """Самодеятельность в простое: гуляем, балуемся, учим слова."""
        if self.one_shot or self.walk_target is not None:
            return
        idle_for = system_idle_seconds()
        if idle_for > self.policy.walk_after_idle and now >= self.next_walk_at:
            # Прогулка по всем мониторам: область - весь виртуальный экран.
            delta = self.policy.walk_delta(
                self.window.pos_x + (self.window.win_w - self.window.cat_w),
                self.screen.all.left,
                self.screen.all.right - self.window.cat_w,
            )
            if delta:
                self.walk_target = self.window.pos_x + delta
                self.state = "running_left" if delta < 0 else "running_right"
                self.frame = 0
            self.next_walk_at = now + self.policy.next_walk_delay()
            return
        if now >= self.next_word_at and idle_for > 20:
            # Раз в несколько минут сам показывает карточку со словом.
            self.show_word()
            self.next_word_at = now + self.policy.next_word_delay()
            return
        if now >= self.next_fun_at:
            self._play_once(self._rng_choice(
                ["idle_random_1", "idle_random_2", "paw_wave", "fish_snack"]))
            self.next_fun_at = now + self.policy.next_fun_delay()

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
            # Идём к цели: 3 пикселя на кадр.
            direction = 1 if self.walk_target > self.window.pos_x else -1
            self.window.pos_x += direction * 3 * steps
            done = (direction > 0 and self.window.pos_x >= self.walk_target) or \
                   (direction < 0 and self.window.pos_x <= self.walk_target)
            if done:
                self.window.pos_x = self.walk_target
                self.walk_target = None
                self.state = "idle"
                self.frame = 0
        if self.one_shot:
            self.frame += steps
            if self.frame >= self.atlas.info(self.state).frames:
                self.one_shot = None
                self.state = "idle"
                self.frame = 0
        else:
            self.frame = (self.frame + steps) % self.atlas.info(self.state).frames

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
        now = time.monotonic()
        self._amuse_self(now)
        self._advance_frame(now)
        if self._card_image is not None and now >= self._card_until:
            self.hide_word()
        cat_frame = self.atlas.frames(self.state)[self.frame]
        self.renderer.push(self.window.hwnd, self._compose(cat_frame),
                           self.window.pos_x, self.window.pos_y)
        if self._running:
            self.window.root.after(TICK_MS, self._tick_safe)

    def _tick_safe(self) -> None:
        try:
            self.tick()
        except Exception:
            import traceback
            self._log(traceback.format_exc())
            raise

    def _exit(self) -> None:
        self._running = False
        self.speaker.close()
        self.window.root.destroy()

    def run(self) -> None:
        self._running = True
        self._log(f"старт, hwnd={self.window.hwnd}, "
                  f"позиция={self.window.pos_x},{self.window.pos_y}, "
                  f"экраны: {self.screen.all}")
        self.tick()
        self.window.root.mainloop()
