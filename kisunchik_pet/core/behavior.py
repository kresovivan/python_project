# -*- coding: utf-8 -*-
"""Политика поведения питомца: когда гулять, когда баловаться,
когда показывать слово.

Что это в жизни: "характер котика на бумаге". Класс ничего не рисует
и не двигает - он только решает. Поэтому его легко проверять тестами:
подали время и простой - получили решение.
"""

import random


class BehaviorPolicy:
    """Решает, что питомец делает дальше в простое."""

    def __init__(
        self,
        walk_after_idle: float = 15.0,
        sleep_after_idle: float = 180.0,
        fun_period=(25.0, 55.0),
        word_period=(300.0, 600.0),
        walk_span=(150, 450),
        walk_delay=(30.0, 80.0),
        rng: random.Random | None = None,
    ):
        # walk_after_idle - сколько секунд тишины ждать перед прогулкой
        # sleep_after_idle - после стольких секунд тишины котик засыпает
        self.walk_after_idle = walk_after_idle
        self.sleep_after_idle = sleep_after_idle
        self.fun_period = fun_period
        self.word_period = word_period
        self.walk_span = walk_span
        self.walk_delay = walk_delay
        self._rng = rng or random.Random()

    def next_walk_delay(self) -> float:
        return self._rng.uniform(*self.walk_delay)

    def next_fun_delay(self) -> float:
        return self._rng.uniform(*self.fun_period)

    def next_word_delay(self) -> float:
        return self._rng.uniform(*self.word_period)

    def walk_delta(self, pos_x: int, area_left: int, area_right: int) -> int:
        """На сколько пикселей прогуляться, не выходя за края области.

        area_left, area_right - допустимый диапазон левой координаты окна
        (обычно весь виртуальный экран, чтобы котик ходил на все мониторы).
        """
        span = self._rng.choice([-1, 1]) * self._rng.randint(*self.walk_span)
        target = max(area_left, min(area_right, pos_x + span))
        return target - pos_x
