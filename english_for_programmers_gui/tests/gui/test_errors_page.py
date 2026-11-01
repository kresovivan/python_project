# Страница "Читаем ошибки": сообщение Python, по пробелу перевод и разбор.

import unittest

from tests.gui.base import GuiTestCase

P_KEY = 80


class ErrorsPageTestCase(GuiTestCase):
    def setUp(self):
        super().setUp()
        self.page = self.open_page("errors")


class ErrorsPageTests(ErrorsPageTestCase):
    def test_space_shows_translation(self):
        self.press("space")

        self.assertTrue(self.page.revealed)
        self.assertTrue(self.page.rows["ru"].cget("text"))

    def test_right_arrow_after_last_error_shows_first(self):
        self.page.index = len(self.page.errors) - 1

        self.press("Right")

        self.assertEqual(self.page.index, 0)

    def test_left_arrow_before_first_error_shows_last(self):
        self.page.index = 0

        self.press("Left")

        self.assertEqual(self.page.index, len(self.page.errors) - 1)

    def test_current_error_is_remembered(self):
        self.press("Right")

        self.assertEqual(self.app.settings.get("errors_index"), self.page.index)

    def test_p_speaks_error_message(self):
        self.press("з", P_KEY)

        self.assertEqual(
            self.spoken[-1], (self.page.errors[self.page.index].message, False)
        )


if __name__ == "__main__":
    unittest.main()
