# Расчёт окна под монитор (gui/screen.py) - чистая математика, без окна.
#
# Monitor(left, top, width, height, scale): рабочая область в пикселях
# и масштаб Windows (2.0 - это 200%).

import unittest

from gui.screen import BIG_UI, SMALL_UI, Monitor, parse_geometry, plan_window

LAPTOP = Monitor(0, 0, 1366, 728, 1.0)
FULL_HD = Monitor(0, 0, 1920, 1040, 1.0)
UHD_200 = Monitor(0, 0, 3840, 2040, 2.0)  # основной монитор пользователя
UHD_100 = Monitor(0, 0, 3840, 2160, 1.0)
RIGHT_TOP = Monitor(3840, -484, 3072, 1800, 2.0)  # второй монитор: правее и выше


class ParseGeometryTests(unittest.TestCase):
    def test_geometry_string_is_split_into_numbers(self):
        self.assertEqual(parse_geometry("1200x780+150+90"), (1200, 780, 150, 90))

    def test_negative_position_is_allowed(self):
        """Монитор может быть выше основного: тогда y меньше нуля."""
        self.assertEqual(parse_geometry("1200x780+3840+-484"), (1200, 780, 3840, -484))

    def test_wrong_string_gives_none(self):
        self.assertIsNone(parse_geometry("bad"))

    def test_missing_string_gives_none(self):
        self.assertIsNone(parse_geometry(None))


class InterfaceScaleTests(unittest.TestCase):
    def test_small_screen_gets_smaller_interface(self):
        scale = plan_window(LAPTOP).ui_scale

        self.assertLess(scale, 1.0)
        self.assertGreaterEqual(scale, SMALL_UI)

    def test_large_screen_without_windows_scaling_gets_bigger_interface(self):
        self.assertEqual(plan_window(UHD_100).ui_scale, BIG_UI)

    def test_screen_scaled_by_windows_keeps_normal_interface(self):
        """При 200% Windows уже всё увеличила, второй раз увеличивать не нужно."""
        self.assertEqual(plan_window(UHD_200).ui_scale, 1.0)


class WindowPlacementTests(unittest.TestCase):
    def assert_window_inside(
        self, monitor: Monitor, geometry: str, ui_scale: float
    ) -> None:
        """Окно целиком на мониторе. Своя проверка: её используют несколько тестов."""
        width, height, x, y = parse_geometry(geometry)
        pixels_per_unit = monitor.scale * ui_scale
        self.assertGreaterEqual(x, monitor.left)
        self.assertGreaterEqual(y, monitor.top)
        self.assertLessEqual(
            x + width * pixels_per_unit, monitor.left + monitor.width + 1
        )
        self.assertLessEqual(
            y + height * pixels_per_unit, monitor.top + monitor.height + 1
        )

    def test_new_window_fits_every_monitor(self):
        for monitor in (LAPTOP, FULL_HD, UHD_200, UHD_100, RIGHT_TOP):
            with self.subTest(monitor=monitor):
                plan = plan_window(monitor)

                self.assert_window_inside(monitor, plan.geometry, plan.ui_scale)

    def test_saved_window_is_restored_when_it_fits(self):
        original = plan_window(RIGHT_TOP)

        restored = plan_window(
            RIGHT_TOP, {"geometry": original.geometry, "maximized": False}
        )

        self.assertEqual(restored.geometry, original.geometry)

    def test_saved_window_from_other_monitor_is_moved_onto_this_one(self):
        """Окно запомнили на мониторе, которого сейчас нет: его нельзя потерять."""
        plan = plan_window(
            FULL_HD, {"geometry": "1200x780+5000+100", "maximized": False}
        )

        self.assert_window_inside(FULL_HD, plan.geometry, plan.ui_scale)

    def test_maximized_state_is_restored(self):
        plan = plan_window(FULL_HD, {"geometry": "1200x780+100+100", "maximized": True})

        self.assertTrue(plan.maximized)


if __name__ == "__main__":
    unittest.main()
