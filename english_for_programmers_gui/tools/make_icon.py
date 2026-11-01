# =============================================================================
# РИСУЕМ ЗНАЧОК ПРОГРАММЫ (assets/icon.ico) - без графических редакторов
# =============================================================================
#
# Значок в стиле программы: тёмный квадрат со скруглёнными углами, на нём
# три светящиеся "стеклянные" плоскости (СЛОВО, ПЕРЕВОД, ПРАКТИКА) и
# яркое ядро в центре - как анимированная схема на главной странице.
#
# Как это работает:
#   1. Картинку считаем как массив чисел numpy: для каждого пикселя - цвет и
#      прозрачность. Фигуры (ромбы, круги) задаём формулами.
#   2. Чтобы края были гладкими, рисуем в 8 раз крупнее и потом усредняем
#      каждые 8x8 пикселей в один (сглаживание, "суперсэмплинг").
#   3. Каждый размер (16, 24, 32 ... 256 пикселей) сохраняем как PNG, а все PNG
#      складываем в один файл .ico - Windows сама выбирает нужный размер.
#
# Запуск:  python tools/make_icon.py   (из папки программы)

import struct
import zlib
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
SIZES = [16, 24, 32, 48, 64, 128, 256]
SUPERSAMPLE = 8


def rgb(hex_color: str) -> np.ndarray:
    """"#a6c2f5" превращается в массив [166, 194, 245] (числа от 0 до 255)."""
    return np.array([int(hex_color[i : i + 2], 16) for i in (1, 3, 5)], dtype=float)


class IconPainter:
    """Рисует значок нужного размера. Холст - массивы цвета и прозрачности."""

    # Цвета - из gui/theme.py (тёмная тема).
    BG_TOP = rgb("#151d2c")
    BG_BOTTOM = rgb("#0a0a0b")
    PLANES = (rgb("#1b2f52"), rgb("#13213a"), rgb("#0f1b2e"))  # верх, середина, низ (кортеж: не меняется)
    EDGE = rgb("#a6c2f5")
    GLOW = rgb("#5f8cf1")
    CORE = rgb("#e6f0ff")

    def __init__(self, size: int):
        self.size = size
        n = size * SUPERSAMPLE
        # Координаты каждого пикселя от 0 до 1: x - вправо, y - вниз.
        ys, xs = np.mgrid[0:n, 0:n]
        self.x = (xs + 0.5) / n
        self.y = (ys + 0.5) / n
        self.color = np.zeros((n, n, 3))
        self.alpha = np.zeros((n, n))
        # Маленькие значки рисуем "крупнее": тонкие детали на 16 пикселях не видны.
        self.bold = 1.0 if size >= 48 else (1.6 if size >= 24 else 2.2)

    # --- рисование ----------------------------------------------------------------

    def paint(self, color: np.ndarray, coverage: np.ndarray) -> None:
        """Наложить цвет поверх текущей картинки с прозрачностью coverage (0-1)."""
        coverage = np.clip(coverage, 0, 1)
        self.color = self.color * (1 - coverage[..., None]) + color * coverage[..., None]
        self.alpha = self.alpha + coverage * (1 - self.alpha)

    def rounded_square(self) -> np.ndarray:
        """Маска квадрата со скруглёнными углами (как значки Windows 11)."""
        r, pad = 0.2, 0.03
        dx = np.maximum(np.abs(self.x - 0.5) - (0.5 - pad - r), 0)
        dy = np.maximum(np.abs(self.y - 0.5) - (0.5 - pad - r), 0)
        return (dx**2 + dy**2 <= r**2).astype(float)

    def diamond(self, cy: float, a: float, b: float) -> tuple[np.ndarray, np.ndarray]:
        """Ромб с центром (0.5, cy). Возвращает: заливку и тонкий контур."""
        d = np.abs(self.x - 0.5) / a + np.abs(self.y - cy) / b  # 1 - ровно на границе ромба
        fill = (d <= 1).astype(float)
        width = 0.012 * self.bold / b  # толщина контура
        edge = (np.abs(d - 1) <= width).astype(float)
        return fill, edge

    def glow(self, cx: float, cy: float, radius: float, squash: float = 1.0) -> np.ndarray:
        """Мягкое свечение: яркое в центре, плавно гаснет к краям."""
        dist = np.sqrt((self.x - cx) ** 2 + ((self.y - cy) / squash) ** 2)
        return np.exp(-((dist / radius) ** 2))

    def draw(self) -> None:
        square = self.rounded_square()
        # Фон: вертикальный градиент от синевато-тёмного к почти чёрному.
        background = self.BG_TOP + (self.BG_BOTTOM - self.BG_TOP) * self.y[..., None]
        self.color = background
        self.alpha = square

        # Голубое пятно света за плоскостями.
        self.paint(self.GLOW, 0.35 * self.glow(0.5, 0.52, 0.32, squash=0.8) * square)

        a, b = 0.34, 0.34 * 0.42  # половина ширины и высоты ромба
        step = b * 1.55
        levels = [0.52 - step, 0.52, 0.52 + step]

        # Светящаяся вертикальная линия через центры плоскостей.
        line = np.exp(-((self.x - 0.5) / (0.012 * self.bold)) ** 2) * (self.y > levels[0]) * (self.y < levels[2])
        self.paint(self.EDGE, 0.7 * line * square)

        # Плоскости снизу вверх: верхняя ложится поверх нижних.
        for index in (2, 1, 0):
            fill, edge = self.diamond(levels[index], a, b)
            self.paint(self.PLANES[index], 0.95 * fill * square)
            # Верхние грани ярче - будто свет падает сверху ("стекло").
            top_half = (self.y <= levels[index]).astype(float)
            self.paint(self.EDGE, edge * (0.55 + 0.45 * top_half) * square)

        # Ядро на средней плоскости: свечение и яркая точка.
        self.paint(self.GLOW, 0.8 * self.glow(0.5, levels[1], 0.09 * self.bold, squash=0.7) * square)
        core_r = 0.035 * self.bold
        core = np.clip((core_r - np.hypot(self.x - 0.5, self.y - levels[1])) * self.size * SUPERSAMPLE, 0, 1)
        self.paint(self.CORE, core * square)

    # --- результат ----------------------------------------------------------------

    def rgba(self) -> np.ndarray:
        """Уменьшить в SUPERSAMPLE раз (усреднить блоки) и вернуть картинку RGBA 0-255."""
        s, k = self.size, SUPERSAMPLE
        premultiplied = self.color * self.alpha[..., None]
        color = premultiplied.reshape(s, k, s, k, 3).mean(axis=(1, 3))
        alpha = self.alpha.reshape(s, k, s, k).mean(axis=(1, 3))
        safe = np.where(alpha > 0, alpha, 1)[..., None]
        image = np.dstack([color / safe, alpha * 255])
        return np.clip(np.round(image), 0, 255).astype(np.uint8)


def png_bytes(image: np.ndarray) -> bytes:
    """Закодировать картинку RGBA в формат PNG (стандартная библиотека: zlib + struct)."""
    height, width, _ = image.shape

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)  # 8 бит, RGBA
    rows = b"".join(b"\x00" + image[y].tobytes() for y in range(height))  # 0 - без фильтра
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b"")


def ico_bytes(pngs: dict[int, bytes]) -> bytes:
    """Собрать файл .ico: заголовок, таблица размеров и сами PNG-картинки."""
    header = struct.pack("<HHH", 0, 1, len(pngs))  # 1 - это значок (icon)
    offset = 6 + 16 * len(pngs)
    table, data = b"", b""
    for size, png in pngs.items():
        side = 0 if size >= 256 else size  # 0 в формате ICO означает 256
        table += struct.pack("<BBBBHHII", side, side, 0, 0, 1, 32, len(png), offset + len(data))
        data += png
    return header + table + data


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    pngs = {}
    for size in SIZES:
        painter = IconPainter(size)
        painter.draw()
        pngs[size] = png_bytes(painter.rgba())
    (ASSETS / "icon.ico").write_bytes(ico_bytes(pngs))
    (ASSETS / "icon.png").write_bytes(pngs[256])  # для просмотра и для окна программы
    print(f"Готово: {ASSETS / 'icon.ico'} ({len(pngs)} размеров)")


if __name__ == "__main__":
    main()
