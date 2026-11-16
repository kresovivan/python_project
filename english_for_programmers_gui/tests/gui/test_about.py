# Страница "Об авторе" (gui/pages/about.py).

import tkinter as tk
import unittest
from unittest.mock import patch

from gui.pages.about import PROJECT_URL
from tests.gui.base import GuiTestCase

ZERO_KEY = 48  # номер физической клавиши 0


def all_texts(widget) -> str:
    """Весь текст, который видно на виджете и внутри него, одной строкой.

    winfo_children() - дочерние виджеты. Обходим их все, вглубь,
    и собираем надписи (cget("text")) у тех, у кого они есть.
    """
    texts = []
    try:
        texts.append(str(widget.cget("text")))
    # У рамок надписи нет: tkinter отвечает TclError, CustomTkinter - ValueError.
    except (tk.TclError, ValueError):
        pass
    for child in widget.winfo_children():
        texts.append(all_texts(child))
    return "\n".join(texts)


class AboutTestCase(GuiTestCase):
    def setUp(self):
        super().setUp()
        self.page = self.open_page("about")
        self.text = all_texts(self.page)


class MenuTests(AboutTestCase):
    def test_about_page_is_last_in_menu_and_opens_with_ctrl_0(self):
        """Пунктов меню 10, а цифр 9: десятый пункт открывает Ctrl+0."""
        self.open_page("home")

        self.press("0", ZERO_KEY, ctrl=True)

        self.assertEqual(self.app.host.keys[-1], "about")
        self.assertEqual(self.app.current.key, "about")


class ContentTests(AboutTestCase):
    def test_author_and_coauthor_are_named(self):
        self.assertIn("Kresov Ivan", self.text)
        self.assertIn("Claude Code", self.text)

    def test_project_size_is_taken_from_dictionary(self):
        """Число слов не вписано в текст руками: добавят слово - число обновится."""
        self.assertIn(str(len(self.app.vocabulary)), self.text)


class ProjectLinkTests(AboutTestCase):
    def test_button_opens_project_on_github(self):
        with patch("gui.pages.about.webbrowser.open") as open_in_browser:
            self.page.open_project()

        open_in_browser.assert_called_once_with(PROJECT_URL)


if __name__ == "__main__":
    unittest.main()
