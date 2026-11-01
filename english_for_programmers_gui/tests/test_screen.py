import sys
import unittest

from gui.screen import Monitor, Screens, parse_geometry, plan_window


class ScreenTests(unittest.TestCase):
    def test_parse_geometry(self):
        self.assertEqual(parse_geometry("1200x780+150+-90"), (1200, 780, 150, -90))
        self.assertEqual(parse_geometry("1200x780+3840+-484"), (1200, 780, 3840, -484))
        self.assertIsNone(parse_geometry("bad"))
        self.assertIsNone(parse_geometry(None))

    def test_window_fits_different_monitors(self):
        cases = [
            Monitor(0, 0, 1366, 728, 1.0),
            Monitor(0, 0, 1920, 1040, 1.0),
            Monitor(0, 0, 1920, 1040, 1.5),
            Monitor(0, 0, 3840, 2040, 2.0),
            Monitor(0, 0, 3840, 2160, 1.0),
            Monitor(3840, -484, 3072, 1800, 2.0),
        ]
        for monitor in cases:
            with self.subTest(monitor=monitor):
                plan = plan_window(monitor)
                parsed = parse_geometry(plan.geometry)
                self.assertIsNotNone(parsed)
                width, height, x, y = parsed
                pixels_per_unit = monitor.scale * plan.ui_scale
                physical_width = width * pixels_per_unit
                physical_height = height * pixels_per_unit
                self.assertLessEqual(physical_width, monitor.width + 1)
                self.assertLessEqual(physical_height, monitor.height + 1)
                self.assertGreaterEqual(x, monitor.left)
                self.assertLessEqual(x + physical_width, monitor.left + monitor.width + 1)
                self.assertGreaterEqual(y, monitor.top)
                self.assertLessEqual(y + physical_height, monitor.top + monitor.height + 1)

    def test_saved_window_is_restored(self):
        monitor = Monitor(3840, -484, 3072, 1800, 2.0)
        original = plan_window(monitor)
        restored = plan_window(monitor, {"geometry": original.geometry, "maximized": False})
        self.assertEqual(restored.geometry, original.geometry)

    @unittest.skipUnless(sys.platform == "win32", "Нужны мониторы Windows")
    def test_real_monitors_are_detected(self):
        self.assertTrue(Screens.all())


if __name__ == "__main__":
    unittest.main()
