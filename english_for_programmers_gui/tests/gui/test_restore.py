# Продолжение занятия после перезапуска программы.

import unittest

from tests.gui.base import GuiTestCase
from tests.support import pump


class RestoreTests(GuiTestCase):
    def leave_typing_unfinished(self) -> str:
        """Начать "Написание слова", ответить на одно слово и вернуть следующее слово."""
        page = self.open_page("typing")
        page.start_new()
        page.entry.insert(0, "wrong")
        page.submit()
        saved = self.app.settings.session("typing")
        return saved.keys[saved.index]

    def test_home_page_offers_to_continue_unfinished_lesson(self):
        self.leave_typing_unfinished()

        home = self.open_page("home")

        self.assertTrue(home.hero_button.cget("text").startswith("Продолжить"))

    def test_enter_after_restart_continues_from_same_word(self):
        expected = self.leave_typing_unfinished()
        self.app.on_close()

        second = self.open_app()  # тот же user_data - как следующий запуск программы
        self.press("Return", app=second)
        pump(second)

        self.assertEqual(second.current.key, "typing")
        self.assertEqual(second.pages["typing"].word.en, expected)


if __name__ == "__main__":
    unittest.main()
