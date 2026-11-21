# -*- coding: utf-8 -*-
"""Тесты пузыря: картинка собирается, текст не вылезает за края.

Главное правило пузыря: шрифт не уменьшается, растёт сам пузырь -
сначала в ширину (min_width..max_width), потом в высоту переносами.
"""

import unittest

import numpy as np

from core.bubble import (BubbleImage, TITLE_SIZE, TEXT_SIZE, _fit_font, _font,
                         _wrap, _wrap_hard, FONT_REGULAR, FONT_BOLD)
from PIL import Image, ImageDraw


class TestBubbleImage(unittest.TestCase):
    def setUp(self):
        self.maker = BubbleImage(min_width=340, max_width=760)

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

    def test_long_title_grows_bubble(self):
        """Длинный заголовок: пузырь растёт в ширину, шрифт не мельчает."""
        img = self.maker.render("expensive (computational)", "икспэнсив",
                                "затратный")
        self.assertGreater(img.size[0], 340)
        self.assertLessEqual(img.size[0], 760)

    def test_growth_has_limit(self):
        """Очень длинный текст не раздувает пузырь больше max_width."""
        img = self.maker.render(
            "слово " * 60, "подзаголовок " * 30, "перевод " * 80)
        self.assertLessEqual(img.size[0], 760)

    def test_long_single_word_wraps_by_chars(self):
        """Неразрывное длинное слово режется посимвольно, не вылезает."""
        probe = Image.new("RGBA", (10, 10))
        d = ImageDraw.Draw(probe)
        font = _font(FONT_BOLD, TITLE_SIZE)
        lines = _wrap_hard(d, "internationalization", font, 200)
        self.assertGreater(len(lines), 1)
        for line in lines:
            self.assertLessEqual(d.textlength(line, font=font), 201)

    def test_height_grows_with_lines(self):
        """Много строк - выше пузырь."""
        short = self.maker.render("cat", "кэт", "кот")
        tall = self.maker.render("cat", "кэт", "очень " * 40 + "длинный перевод")
        self.assertGreater(tall.size[1], short.size[1])


if __name__ == "__main__":
    unittest.main()
