# -*- coding: utf-8 -*-
"""Пузырь с текстом, который питомец показывает рядом с собой.

Что это в жизни: "облачко из комикса". Рисуется как картинка PIL:
белое облачко со скруглёнными углами, хвостик из кружков к котику,
блик слева сверху. Текст подгоняется под размер, чтобы не вылезал
за края - это главная боль при рисовании текстовых пузырей.
"""

from PIL import Image, ImageDraw, ImageFont

# Системные шрифты Windows - они есть всегда.
FONT_REGULAR = r"C:\Windows\Fonts\segoeui.ttf"
FONT_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"


def _font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def _fit_font(draw, text, path, max_size, max_width, min_size=10):
    """Подбирает размер шрифта, чтобы текст влез в max_width."""
    size = max_size
    while size > min_size:
        f = _font(path, size)
        w = f.getbbox(text)[2]
        if w <= max_width:
            return f
        size -= 1
    return _font(path, min_size)


def _wrap(draw, text, font, max_width):
    """Разбивает текст на строки по ширине пузыря."""
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = (current + " " + word).strip()
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


class BubbleImage:
    """Строит картинку пузыря с заголовком и строками текста."""

    def __init__(self, width: int = 340, padding: int = 18):
        self.width = width
        self.padding = padding

    def render(self, title: str, subtitle: str, lines_text: str,
               tail: str = "bottom-right") -> Image.Image:
        """Картинка RGBA: пузырь с заголовком, подзаголовком и текстом.

        tail - куда смотрит хвостик: "bottom-right" (к котику справа снизу)
        или "bottom" (по центру снизу).
        """
        pad = self.padding
        max_text_w = self.width - 2 * pad

        probe = Image.new("RGBA", (10, 10))
        d = ImageDraw.Draw(probe)

        f_title = _fit_font(d, title, FONT_BOLD, 30, max_text_w)
        f_sub = _fit_font(d, subtitle, FONT_REGULAR, 18, max_text_w) if subtitle else None
        f_text = _font(FONT_REGULAR, 17)
        text_lines = _wrap(d, lines_text, f_text, max_text_w) if lines_text else []

        # Считаем высоту содержимого.
        h = pad
        h += f_title.getbbox(title)[3] + 4
        if f_sub:
            h += f_sub.getbbox(subtitle)[3] + 4
        for line in text_lines:
            h += f_text.getbbox(line)[3] + 3
        h += pad

        tail_h = 26  # место под хвостик снизу
        img = Image.new("RGBA", (self.width, h + tail_h), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)

        # Тело пузыря: белое облачко с мягкой обводкой.
        body = (0, 0, self.width, h)
        d.rounded_rectangle(body, radius=22, fill=(255, 255, 255, 245),
                            outline=(190, 200, 215, 255), width=2)
        # Блик слева сверху - как у мыльного пузыря. Рисуем ДО текста,
        # чтобы буквы всегда были поверх блика.
        d.ellipse((10, 8, 52, 30), fill=(220, 235, 255, 110))

        # Хвостик из двух кружков к котику.
        if tail == "bottom-right":
            cx = self.width - 60
        else:
            cx = self.width // 2
        d.ellipse((cx - 9, h - 6, cx + 9, h + 12),
                  fill=(255, 255, 255, 245), outline=(190, 200, 215, 255), width=2)
        d.ellipse((cx + 10, h + 10, cx + 24, h + 24),
                  fill=(255, 255, 255, 245), outline=(190, 200, 215, 255), width=2)

        # Текст.
        y = pad
        d.text((pad, y), title, font=f_title, fill=(30, 40, 60, 255))
        y += f_title.getbbox(title)[3] + 4
        if f_sub:
            d.text((pad, y), subtitle, font=f_sub, fill=(110, 120, 140, 255))
            y += f_sub.getbbox(subtitle)[3] + 4
        for line in text_lines:
            d.text((pad, y), line, font=f_text, fill=(45, 55, 75, 255))
            y += f_text.getbbox(line)[3] + 3
        return img
