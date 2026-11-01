# =============================================================================
# МОНИТОРЫ И РАЗМЕР ОКНА - подгон под экран, на котором запускают программу
# =============================================================================
#
# Что это в жизни:
#   Monitor    - "паспорт монитора": где он стоит, какого размера, какой масштаб;
#   WindowPlan - "план расстановки": какого размера открыть окно и где;
#   Screens    - "справочное бюро Windows": отвечает, какие мониторы подключены.
# Расчёт (plan_window) - чистая математика, её проверяют быстрые тесты
# (tests/unit/test_screen.py). Вызывает всё это окно App при запуске.
#
# Что делает:
#   1. Узнаёт у Windows список мониторов: рабочую область (экран без панели
#      задач) и масштаб (100%, 125%, 200% ...).
#   2. Выбирает монитор: где было окно в прошлый раз (если он ещё подключён
#      и окно на нём помещается) или где сейчас указатель мыши - там, где
#      человек щёлкнул по ярлыку.
#   3. Считает размер окна и масштаб интерфейса под этот монитор.
#
# Единицы измерения (важно, легко запутаться):
#   - пиксели монитора ("физические") - координаты и размеры экрана;
#   - логические единицы - в них заданы размеры интерфейса. CustomTkinter
#     умножает их на масштаб Windows: 1200 логических при 200% = 2400 пикселей.
#   В geometry() CustomTkinter ширину и высоту задают в логических единицах,
#   а положение x, y - в пикселях монитора.
#
# Расчёт (plan_window) - обычная функция без окна: её легко проверить на
# любых "воображаемых" мониторах.

import ctypes
import re
import sys
from dataclasses import dataclass

DESIGN_SIZE = (1200, 780)  # удобный размер окна в логических единицах
MIN_SIZE = (1050, 760)  # меньше - интерфейс перестаёт помещаться
LARGE_SIZE = (1440, 900)  # на просторном мониторе окно можно сделать больше
SMALL_UI = 0.7  # меньше этого масштаба интерфейс уже не уменьшаем - текст станет нечитаемым
BIG_UI = 1.2  # насколько увеличить интерфейс на огромном экране без масштаба Windows


@dataclass(frozen=True)
class Monitor:
    """Монитор: рабочая область в пикселях и масштаб Windows (2.0 - это 200%)."""

    left: int
    top: int
    width: int
    height: int
    scale: float = 1.0

    @property
    def logical_width(self) -> float:
        return self.width / self.scale

    @property
    def logical_height(self) -> float:
        return self.height / self.scale

    def contains(self, x: int, y: int) -> bool:
        return self.left <= x < self.left + self.width and self.top <= y < self.top + self.height


@dataclass(frozen=True)
class WindowPlan:
    """Результат расчёта: как открыть окно."""

    width: int  # логические единицы
    height: int
    x: int  # пиксели монитора
    y: int
    ui_scale: float  # масштаб интерфейса: 1.0 - как задумано, 0.8 - мельче
    min_width: int
    min_height: int
    maximized: bool = False

    @property
    def geometry(self) -> str:
        return f"{self.width}x{self.height}+{self.x}+{self.y}"


# =============================================================================
# Расчёт - без окна и без Windows API
# =============================================================================


def parse_geometry(text: str | None) -> tuple[int, int, int, int] | None:
    """"1200x780+150+90" превращается в (1200, 780, 150, 90). Неверная строка - None."""
    match = re.fullmatch(r"(\d+)x(\d+)\+(-?\d+)\+(-?\d+)", text or "")
    return tuple(int(v) for v in match.groups()) if match else None


def ui_scale_for(monitor: Monitor) -> float:
    """Масштаб интерфейса под монитор.

    Маленький экран (ноутбук 1366x768) - уменьшаем, чтобы окно поместилось.
    Огромный экран без масштаба Windows (4K при 100%) - чуть увеличиваем,
    иначе текст будет мелким. Всё остальное - 1.0, как задумано.
    """
    room_w = monitor.logical_width * 0.96  # небольшой запас по краям
    room_h = monitor.logical_height * 0.96
    # Уменьшаем так, чтобы помещался УДОБНЫЙ размер окна (DESIGN_SIZE), а не только
    # минимальный: при минимальном нижние кнопки на главной слегка сплющиваются.
    if room_w < DESIGN_SIZE[0] or room_h < DESIGN_SIZE[1]:
        return round(max(SMALL_UI, min(room_w / DESIGN_SIZE[0], room_h / DESIGN_SIZE[1])), 2)
    # Увеличиваем сами, только если Windows не масштабирует (100%): при 125-200%
    # Windows уже увеличила интерфейс, и второй раз увеличивать не нужно.
    if monitor.scale <= 1.0 and monitor.logical_width >= 2400 and monitor.logical_height >= 1350:
        return BIG_UI
    return 1.0


def plan_window(monitor: Monitor, saved: dict | None = None) -> WindowPlan:
    """Рассчитать окно для монитора.

    saved - то, что запомнили в прошлый раз: {"geometry": "1200x780+150+90",
    "maximized": False}. Используется, только если окно целиком помещается
    на этом мониторе; иначе - размер по монитору и окно по центру.
    """
    ui = ui_scale_for(monitor)
    pixels_per_unit = monitor.scale * ui  # во сколько пикселей превращается одна логическая единица
    # Сколько логических единиц помещается на мониторе при таком масштабе.
    room_w = monitor.width / pixels_per_unit
    room_h = monitor.height / pixels_per_unit
    min_w = round(min(MIN_SIZE[0], room_w * 0.96))
    min_h = round(min(MIN_SIZE[1], room_h * 0.96))
    maximized = bool(saved and saved.get("maximized"))

    old = parse_geometry(saved.get("geometry")) if saved else None
    if old:
        w, h, x, y = old
        fits = min_w <= w <= room_w and min_h <= h <= room_h
        # Левый верхний угол (с небольшим отступом) должен быть на этом мониторе.
        if fits and monitor.contains(x + 40, y + 20) and monitor.contains(x + round(w * pixels_per_unit) - 40, y + 20):
            return WindowPlan(w, h, x, y, ui, min_w, min_h, maximized)

    # Новый размер: на просторном мониторе - побольше; ширина не больше 92% экрана,
    # высота не больше 96% (по высоте места обычно меньше, чем по ширине).
    base_w, base_h = LARGE_SIZE if room_w >= LARGE_SIZE[0] / 0.75 and room_h >= LARGE_SIZE[1] / 0.85 else DESIGN_SIZE
    w = round(max(min_w, min(base_w, room_w * 0.92)))
    h = round(max(min_h, min(base_h, room_h * 0.96)))
    # По центру монитора (в пикселях).
    x = monitor.left + round((monitor.width - w * pixels_per_unit) / 2)
    y = monitor.top + round((monitor.height - h * pixels_per_unit) / 2)
    return WindowPlan(w, h, x, y, ui, min_w, min_h, maximized)


# =============================================================================
# Мониторы - спрашиваем у Windows
# =============================================================================


class Screens:
    """Список мониторов и монитор под указателем мыши (Windows API через ctypes)."""

    @staticmethod
    def make_dpi_aware() -> None:
        """Сказать Windows, что программа сама учитывает масштаб каждого монитора.

        Без этого Windows "притворяется", что масштаб 100%, и отдаёт уменьшенные
        размеры экрана (4K при 200% выглядит как 1920x1080). CustomTkinter делает
        то же самое при создании окна, но нам размеры нужны ещё ДО него.
        Повторный вызов безопасен: Windows просто ответит, что уже включено.
        """
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)  # 2 - свой масштаб для каждого монитора
        except (AttributeError, OSError):
            pass

    @staticmethod
    def all() -> list[Monitor]:
        if not sys.platform.startswith("win"):
            return []
        from ctypes import wintypes

        class MONITORINFO(ctypes.Structure):
            _fields_ = [
                ("cbSize", wintypes.DWORD),
                ("rcMonitor", wintypes.RECT),
                ("rcWork", wintypes.RECT),  # рабочая область - без панели задач
                ("dwFlags", wintypes.DWORD),
            ]

        monitors = []

        def collect(handle, _hdc, _rect, _data):
            info = MONITORINFO()
            info.cbSize = ctypes.sizeof(info)
            ctypes.windll.user32.GetMonitorInfoW(handle, ctypes.byref(info))
            dpi_x, dpi_y = wintypes.UINT(), wintypes.UINT()
            try:
                ctypes.windll.shcore.GetDpiForMonitor(handle, 0, ctypes.byref(dpi_x), ctypes.byref(dpi_y))
                scale = dpi_x.value / 96  # 96 точек на дюйм - это 100%
            except (AttributeError, OSError):
                scale = 1.0
            work = info.rcWork
            monitors.append(Monitor(work.left, work.top, work.right - work.left, work.bottom - work.top, scale))
            return True

        callback_type = ctypes.WINFUNCTYPE(
            wintypes.BOOL, wintypes.HMONITOR, wintypes.HDC, ctypes.POINTER(wintypes.RECT), wintypes.LPARAM
        )
        ctypes.windll.user32.EnumDisplayMonitors(None, None, callback_type(collect), 0)
        return monitors

    @staticmethod
    def cursor_position() -> tuple[int, int]:
        from ctypes import wintypes

        point = wintypes.POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
        return point.x, point.y

    @classmethod
    def for_start(cls, saved_geometry: str | None) -> Monitor:
        """Монитор для запуска: где окно было в прошлый раз, иначе - где указатель мыши."""
        monitors = cls.all()
        if not monitors:
            return Monitor(0, 0, 1920, 1040, 1.0)  # не Windows - разумное значение
        old = parse_geometry(saved_geometry)
        if old:
            for monitor in monitors:
                if monitor.contains(old[2] + 40, old[3] + 20):
                    return monitor
        x, y = cls.cursor_position()
        for monitor in monitors:
            if monitor.contains(x, y):
                return monitor
        return monitors[0]
