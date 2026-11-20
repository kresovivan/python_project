# -*- coding: utf-8 -*-
"""Тесты пузыря: картинка собирается, текст не вылезает за края."""

import unittest

import numpy as np

from core.bubble import BubbleImage, _fit_font, _wrap, FONT_REGULAR
from PIL import Image, ImageDraw


class TestBubbleImage(unittest.TestCase):
    def setUp(self):
        self.maker = BubbleImage(width=340)

    def test_render_returns_rgba(self):
        img = self.maker.render("compile", "компайл", "собирать программу из кода")
        self.assertEqual(img.mode, "RGBA")
        self.assertEqual(img.size[0], 340)
        self.assertGreater(img.size[1], 60)

    def test_bubble_is_opaque_inside(self):
        """Внутри пузыря есть плотные белые пиксели."""
        img = self.maker.render("compile", "компайл", "собирать программу")
        alpha = np.asarray(img)[..., 3]
        self.assertGreater(int((alpha > 240).sum()), 5000)

    def test_long_text_wraps_inside(self):
        """Длинный перевод переносится и не выходит за ширину пузыря."""
        probe = Image.new("RGBA", (10, 10))
        d = ImageDraw.Draw(probe)
        from PIL import ImageFont
        font = _fit_font(d, "x", FONT_REGULAR, 17, 300)
        lines = _wrap(d, "очень длинный перевод который не должен вылезать "
                         "за правый край пузыря ни при каких условиях вообще",
                      font, 300)
        for line in lines:
            self.assertLessEqual(d.textlength(line, font=font), 301)
        self.assertGreater(len(lines), 1)

    def test_long_single_word_fits(self):
        """Длинное английское слово ужимается по ширине."""
        img = self.maker.render("internationalization", "интернешнлзейшн",
                                "сделать программу многоязычной")
        self.assertEqual(img.size[0], 340)


if __name__ == "__main__":
    unittest.main()
