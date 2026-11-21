# -*- coding: utf-8 -*-
"""Собрать иконку программы из мордочки котика.

Берём первый кадр idle из атласа, вырезаем голову и кладём её на
тёплую округлую "подставку" - так значок читается и на панели задач,
и на ярлыке. Запуск из папки проекта:

    python tools/make_icon.py

Результат: assets/icon.ico (несколько размеров в одном файле).
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.atlas import SpriteAtlas

ASSETS = Path(__file__).resolve().parent.parent / "assets"
CANVAS = 256
BACKGROUND = (255, 243, 224, 255)  # тёплый кремовый
BORDER = (240, 200, 150, 255)      # мягкая рыжая окантовка
HEAD_PART = 0.55                   # сколько сверху занимает голова


def crop_to_content(img: Image.Image) -> Image.Image:
    """Обрезать прозрачные поля по альфа-каналу."""
    bbox = img.getchannel("A").getbbox()
    return img.crop(bbox) if bbox else img


def load_head() -> Image.Image:
    """Голова котика из первого кадра idle, в полном размере."""
    atlas = SpriteAtlas(ASSETS / "pet.json", ASSETS / "spritesheet.png", 1.0)
    frame = crop_to_content(atlas.frames("idle")[0])
    head = frame.crop((0, 0, frame.width, int(frame.height * HEAD_PART)))
    return crop_to_content(head)


def rounded_background(size: int) -> Image.Image:
    """Кремовый квадрат со скруглёнными углами и тонкой окантовкой."""
    bg = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(bg)
    radius = size // 5
    draw.rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=BACKGROUND)
    draw.rounded_rectangle((2, 2, size - 3, size - 3), radius=radius - 2,
                           outline=BORDER, width=max(2, size // 64))
    return bg


def main() -> None:
    head = load_head()
    margin = int(CANVAS * 0.10)
    inner = CANVAS - margin * 2
    ratio = min(inner / head.width, inner / head.height)
    head = head.resize((int(head.width * ratio), int(head.height * ratio)),
                       Image.LANCZOS)

    icon = rounded_background(CANVAS)
    # Голова чуть приподнята - так мордочка смотрится живее.
    x = (CANVAS - head.width) // 2
    y = (CANVAS - head.height) // 2 - int(CANVAS * 0.02)
    icon.paste(head, (x, y), head)

    icon.save(ASSETS / "icon.png")
    icon.save(ASSETS / "icon.ico",
              sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(f"готово: {ASSETS / 'icon.ico'}")


if __name__ == "__main__":
    main()
