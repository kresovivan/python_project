# -*- coding: utf-8 -*-
"""Пузырь с текстом, который питомец показывает рядом с собой.

Что это в жизни: "облачко из комикса". Рисуется как картинка PIL:
белое облачко со скруглёнными углами, мягкая тень, хвостик из кружков
к котику, блик слева сверху.

Главный принцип: шрифт НИКОГДА не уменьшается. Если текст не влезает,
растёт пузырь - сначала в ширину (от min_width до max_width), потом
в высоту за счёт переноса строк. Читать мелкий текст никто не будет.
"""

from PIL import Image, ImageDraw, ImageFont

# Системные шрифты Windows - они есть всегда.
FONT_REGULAR = r"C:\Windows\Fonts\segoeui.ttf"
FONT_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"

# Фиксированные размеры текста. Менять можно здесь - пузырь подстроится.
TITLE_SIZE = 40
SUBTITLE_SIZE = 24
TEXT_SIZE = 24


def _font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def _fit_font(draw, text, path, max_size, max_width, min_size=10):
    """Подбирает размер шрифта, чтобы текст влез в max_width.

    Осталось для совместимости со старыми вызовами и тестами;
    сам пузырь больше не ужимает текст, а растёт сам.
    """
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


def _wrap_hard(draw, text, font, max_width):
    """Перенос по словам, а слишком длинное слово - посимвольно.

    Чтобы даже "internationalization" в узком пузыре не вылезло
    за край: слово режется на куски по ширине.
    """
    lines = []
    for line in _wrap(draw, text, font, max_width):
        if draw.textlength(line, font=font) <= max_width:
            lines.append(line)
            continue
        piece = ""
        for ch in line:
            if draw.textlength(piece + ch, font=font) <= max_width:
                piece += ch
            else:
                lines.append(piece)
                piece = ch
        if piece:
            lines.append(piece)
    return lines or [""]


class BubbleImage:
    """Строит картинку пузыря с заголовком и строками текста.

    Ширина подбирается под содержимое: минимум min_width, максимум
    max_width. Высота растёт по строкам без ограничений.
    """

    def __init__(self, min_width: int = 470, max_width: int = 780,
                 padding: int = 24):
        self.min_width = min_width
        self.max_width = max_width
        self.padding = padding

    def _natural_width(self, d, parts) -> int:
        """Ширина самой длинной строки при фиксированных шрифтах."""
        widest = 0
        for text, font in parts:
            if text:
                widest = max(widest, int(d.textlength(text, font=font)))
        return widest

    def render(self, title: str, subtitle: str, lines_text: str,
               tail: str = "bottom-right") -> Image.Image:
        """Картинка RGBA: пузырь с заголовком, подзаголовком и текстом.

        tail - куда смотрит хвостик: "bottom-right" (к котику справа снизу)
        или "bottom" (по центру снизу).
        """
        pad = self.padding
        probe = Image.new("RGBA", (10, 10))
        d = ImageDraw.Draw(probe)

        # Шрифты фиксированные - размер букв не зависит от текста.
        f_title = _font(FONT_BOLD, TITLE_SIZE)
        f_sub = _font(FONT_REGULAR, SUBTITLE_SIZE)
        f_text = _font(FONT_REGULAR, TEXT_SIZE)

        # Ширина пузыря: под самую длинную "естественную" строку
        # (заголовок, подзаголовок или самое длинное слово текста),
        # но в рамках min_width..max_width.
        longest_word = max(lines_text.split(), key=len, default="") \
            if lines_text else ""
        natural = self._natural_width(
            d, [(title, f_title), (subtitle, f_sub), (longest_word, f_text)])
        width = min(max(self.min_width, natural + 2 * pad), self.max_width)
        max_text_w = width - 2 * pad

        # Переносим всё, что не влезло в выбранную ширину.
        title_lines = _wrap_hard(d, title, f_title, max_text_w) if title else []
        sub_lines = _wrap_hard(d, subtitle, f_sub, max_text_w) if subtitle else []
        text_lines = _wrap_hard(d, lines_text, f_text, max_text_w) \
            if lines_text else []

        # Считаем высоту содержимого.
        def block_h(lines, font, gap):
            return sum(font.getbbox(line)[3] + gap for line in lines)

        h = pad
        h += block_h(title_lines, f_title, 4)
        h += block_h(sub_lines, f_sub, 4)
        h += block_h(text_lines, f_text, 3)
        h += pad

        tail_h = 26  # место под хвостик снизу
        img = Image.new("RGBA", (width, h + tail_h), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)

        # Мягкая тень под облачком: тот же силуэт, сдвинутый вниз-вправо.
        d.rounded_rectangle((4, 6, width, h + 4), radius=22,
                            fill=(60, 70, 90, 70))

        # Тело пузыря: белое облачко с мягкой обводкой.
        body = (0, 0, width - 4, h)
        d.rounded_rectangle(body, radius=22, fill=(255, 255, 255, 248),
                            outline=(190, 200, 215, 255), width=2)

        # Хвостик из двух кружков к котику.
        if tail == "bottom-right":
            cx = width - 64
        else:
            cx = width // 2
        d.ellipse((cx - 9, h - 6, cx + 9, h + 12),
                  fill=(255, 255, 255, 248), outline=(190, 200, 215, 255), width=2)
        d.ellipse((cx + 10, h + 10, cx + 24, h + 24),
                  fill=(255, 255, 255, 248), outline=(190, 200, 215, 255), width=2)

        # Текст: все строки одного кегля внутри своей роли.
        y = pad
        for line in title_lines:
            d.text((pad, y), line, font=f_title, fill=(30, 40, 60, 255))
            y += f_title.getbbox(line)[3] + 4
        for line in sub_lines:
            d.text((pad, y), line, font=f_sub, fill=(110, 120, 140, 255))
            y += f_sub.getbbox(line)[3] + 4
        for line in text_lines:
            d.text((pad, y), line, font=f_text, fill=(45, 55, 75, 255))
            y += f_text.getbbox(line)[3] + 3
        return img
