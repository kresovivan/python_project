# Цвета оформления (gui/theme.py): выбор цвета по теме и смешивание цветов.

import unittest

import customtkinter as ctk

from gui import theme


class PickTests(unittest.TestCase):
    """pick((светлый, тёмный)) - цвет для текущей темы (для tk.Canvas и tk.Text)."""

    def setUp(self):
        # Тема - общая настройка CustomTkinter: вернём её после теста как было.
        self.addCleanup(ctk.set_appearance_mode, ctk.get_appearance_mode())

    def test_dark_theme_gives_second_color(self):
        ctk.set_appearance_mode("dark")

        self.assertEqual(theme.pick(("#ffffff", "#000000")), "#000000")

    def test_light_theme_gives_first_color(self):
        ctk.set_appearance_mode("light")

        self.assertEqual(theme.pick(("#ffffff", "#000000")), "#ffffff")


class MixTests(unittest.TestCase):
    """mix(a, b, доля) - цвет между a и b: так рисуется "свечение"."""

    def test_zero_gives_first_color(self):
        self.assertEqual(theme.mix("#000000", "#ffffff", 0), "#000000")

    def test_one_gives_second_color(self):
        self.assertEqual(theme.mix("#000000", "#ffffff", 1), "#ffffff")

    def test_half_gives_color_in_the_middle(self):
        self.assertEqual(theme.mix("#000000", "#ffffff", 0.5), "#808080")

    def test_each_channel_is_mixed_separately(self):
        """Красный, зелёный и синий смешиваются каждый сам по себе."""
        self.assertEqual(theme.mix("#ff0000", "#0000ff", 0.5), "#800080")


class PaletteTests(unittest.TestCase):
    def test_every_status_has_color_pair_for_both_themes(self):
        for status, color in theme.STATUS_COLORS.items():
            with self.subTest(status=status):
                self.assertEqual(len(color), 2)


if __name__ == "__main__":
    unittest.main()
