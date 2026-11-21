# -*- coding: utf-8 -*-
"""Тест поведения котика на виртуальном времени.

Главная жалоба была: "котик стоит столбом, не гуляет и не балуется".
Этот тест прогоняет 20 минут виртуальной жизни за долю секунды
и проверяет, что котик реально ходит, машет, ест рыбку и спит.

Часы и датчик бездействия подменяются - поэтому тест быстрый и не
зависит от того, трогает ли кто-то мышку.
"""

import unittest
from pathlib import Path

from gui.app import KisunchikApp

ASSETS = Path(__file__).resolve().parent.parent / "assets"


class FakeClock:
    """Часы, которые идут так быстро, как скажет тест."""

    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class TestPetBehavior(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.clock = FakeClock()
        # Пользователь "активен" (idle=0) - раньше котик в таком режиме
        # ничего не делал вообще, это и был баг.
        cls.app = KisunchikApp(ASSETS, scale=0.5, clock=cls.clock,
                               idle_probe=lambda: 0.0,
                               autostart_sync=lambda on: None)
        # Не рисуем по-настоящему: подменяем отрисовку заглушкой.
        cls.app.renderer.push = lambda *a, **k: True

    @classmethod
    def tearDownClass(cls):
        cls.app.speaker.close()
        cls.app.window.root.destroy()

    def _live(self, seconds):
        """Прожить seconds виртуальных секунд, собирая состояния."""
        seen = []
        end = self.clock.now + seconds
        while self.clock.now < end:
            self.clock.advance(0.1)
            self.app.tick()
            seen.append(self.app.state)
        return seen

    def test_cat_walks_while_user_active(self):
        """Котик гуляет, даже когда пользователь сидит за компьютером."""
        # Отводим котика от края экрана: у края случайная цель прогулки
        # может совпасть с текущей позицией, и прогулка не начнётся.
        self.app.window.pos_x = 1000
        start_x = self.app.window.pos_x
        seen = self._live(240)
        self.assertTrue(
            any(s in ("running_left", "running_right") for s in seen),
            "за 3 минуты котик ни разу не пошёл гулять")
        self.assertNotEqual(self.app.window.pos_x, start_x,
                            "позиция окна не изменилась после прогулки")

    def test_cat_does_fun_tricks(self):
        """Котик балуется: машет лапкой, ест рыбку и т.п."""
        seen = self._live(240)
        fun_states = {"idle_random_1", "idle_random_2", "paw_wave", "fish_snack"}
        done = fun_states & set(seen)
        self.assertTrue(done, "за 4 минуты котик ни разу не побаловался")

    def test_cat_uses_variety(self):
        """За долгое время котик показывает разные затеи, а не одну."""
        seen = self._live(900)
        fun_states = {"idle_random_1", "idle_random_2", "paw_wave", "fish_snack"}
        variety = fun_states & set(seen)
        self.assertGreaterEqual(len(variety), 2,
                                f"котик однообразен: только {variety}")

    def test_one_shot_returns_to_idle(self):
        """После разового трюка котик возвращается в idle."""
        self.app._play_once("somersault")
        seen = self._live(5)
        self.assertIn("somersault", seen)
        self.assertEqual(self.app.state, "idle")
        self.assertIsNone(self.app.one_shot)

    def test_card_hides_after_timeout(self):
        """Карточка со словом сама прячется через CARD_SECONDS."""
        self.app.show_word()
        self.assertIsNotNone(self.app._card_image)
        self._live(12)
        self.assertIsNone(self.app._card_image,
                          "карточка зависла и не скрылась")

    def test_no_redraw_when_nothing_changes(self):
        """Кадр перерисовывается, только если что-то изменилось.

        Это главная защита от "котик ест процессор": раньше окно
        обновлялось 33 раза в секунду даже в полном покое.
        """
        pushes = []
        self.app.renderer.push = lambda *a, **k: pushes.append(1) or True
        # Спокойный idle без сюрпризов: отменяем все запланированные
        # затеи, иначе случайная лапка в середине замера даст лишние
        # (законные) перерисовки и тест будет мерцать.
        self.app.one_shot = None
        self.app.walk_target = None
        self.app.sleeping = False
        self.app.state = "idle"
        self.app.frame = 0
        far = self.clock.now + 10000
        self.app.next_fun_at = far
        self.app.next_walk_at = far
        self.app.next_word_at = far
        # Одна секунда обычного idle: 10 тиков, кадров idle ~6 fps,
        # значит перерисовок должно быть заметно меньше, чем тиков.
        self._live(1.0)
        self.assertLess(len(pushes), 10,
                        f"за 10 тиков было {len(pushes)} перерисовок")


class TestPetSleep(unittest.TestCase):
    def test_cat_sleeps_when_user_away_long(self):
        """Если пользователя долго нет - котик дремлет и засыпает."""
        clock = FakeClock()
        app = KisunchikApp(ASSETS, scale=0.5, clock=clock,
                           idle_probe=lambda: 10000.0,  # давно никого
                           autostart_sync=lambda on: None)
        app.renderer.push = lambda *a, **k: True
        try:
            for _ in range(200):
                clock.advance(0.2)
                app.tick()
            self.assertTrue(app.sleeping, "котик не заснул при долгом простое")
            # Прожить ещё - должен перейти из doze_off в sleeping.
            for _ in range(100):
                clock.advance(0.2)
                app.tick()
            self.assertEqual(app.state, "sleeping")
        finally:
            app.speaker.close()
            app.window.root.destroy()

    def test_cat_wakes_on_click(self):
        """Спящий котик просыпается от клика."""
        clock = FakeClock()
        app = KisunchikApp(ASSETS, scale=0.5, clock=clock,
                           idle_probe=lambda: 10000.0,
                           autostart_sync=lambda on: None)
        app.renderer.push = lambda *a, **k: True
        try:
            for _ in range(300):
                clock.advance(0.2)
                app.tick()
            self.assertTrue(app.sleeping)
            app._on_zone("head")
            self.assertFalse(app.sleeping, "котик не проснулся от клика")
        finally:
            app.speaker.close()
            app.window.root.destroy()

    def test_sleeping_belly_click_still_speaks(self):
        """Клик по животику спящего котика будит его И произносит слово.

        Раньше первый клик только будил котика, а слово не звучало -
        выглядело как "озвучка сломалась".
        """
        clock = FakeClock()
        app = KisunchikApp(ASSETS, scale=0.5, clock=clock,
                           idle_probe=lambda: 10000.0,
                           autostart_sync=lambda on: None)
        app.renderer.push = lambda *a, **k: True
        said = []

        class FakeSpeaker:
            error = None
            def say(self, text):
                said.append(text)
                return True
            def close(self):
                pass

        try:
            for _ in range(300):
                clock.advance(0.2)
                app.tick()
            self.assertTrue(app.sleeping)
            app.speaker.close()
            app.speaker = FakeSpeaker()
            app._on_zone("belly")
            self.assertFalse(app.sleeping)
            self.assertTrue(said, "котик промолчал после клика по животику")
            self.assertIsNotNone(app._card_word, "карточка со словом не появилась")
        finally:
            app.window.root.destroy()


if __name__ == "__main__":
    unittest.main()
