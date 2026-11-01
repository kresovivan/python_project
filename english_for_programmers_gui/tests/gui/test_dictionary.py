# Страница "Словарь": поиск по английскому и русскому, кнопки "Звук".

import unittest

from tests.gui.base import GuiTestCase

P_KEY = 80


class DictionaryTestCase(GuiTestCase):
    def setUp(self):
        super().setUp()
        self.page = self.open_page("dictionary")

    def search(self, text: str) -> None:
        self.page.query.delete(0, "end")
        self.page.query.insert(0, text)
        self.page.search()

    def results_text(self) -> str:
        return self.page.results.text.get("1.0", "end")


class SearchTests(DictionaryTestCase):
    def test_english_word_is_found_ignoring_case(self):
        self.search("LOOP")

        self.assertIn("НАЙДЕНО", self.page.info.cget("text"))
        self.assertIn("loop", self.results_text().lower())

    def test_russian_word_is_found(self):
        self.search("перемен")

        self.assertIn("перемен", self.results_text().lower())

    def test_found_words_have_clickable_sound_buttons(self):
        text = self.page.results.text

        self.search("loop")

        # tag_bind(тег, событие, None) не создаёт привязку, а спрашивает, есть ли она.
        clickable = [
            tag for tag in text.tag_names() if text.tag_bind(tag, "<Button-1>", None)
        ]
        self.assertTrue(clickable)

    def test_letter_p_typed_in_search_field_is_not_spoken(self):
        """В поле поиска P - это буква, а не команда "произнести"."""
        self.page.query.focus_force()
        self.search("loop")

        self.press("з", P_KEY)

        self.assertEqual(self.spoken, [])


class EscapeTests(DictionaryTestCase):
    def test_first_escape_clears_search(self):
        self.search("loop")

        self.press("Escape")

        self.assertEqual(self.app.current.key, "dictionary")
        self.assertEqual(self.page.query.get(), "")

    def test_escape_on_empty_search_returns_home(self):
        self.press("Escape")

        self.assertEqual(self.app.current.key, "home")


if __name__ == "__main__":
    unittest.main()
