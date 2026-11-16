# Страница "Грамматика" (gui/pages/grammar.py): список тем и таблицы.

import unittest

from core.grammar import TOPICS
from tests.gui.base import GuiTestCase


class GrammarTestCase(GuiTestCase):
    def setUp(self):
        super().setUp()
        self.page = self.open_page("grammar")


class TopicTests(GrammarTestCase):
    def test_first_visit_shows_first_topic(self):
        self.assertEqual(self.page.topic_title.cget("text"), TOPICS[0].title)

    def test_click_on_topic_shows_it(self):
        self.page.topic_buttons[2].invoke()

        self.assertEqual(self.page.topic_title.cget("text"), TOPICS[2].title)

    def test_down_arrow_shows_next_topic(self):
        self.press("Down")

        self.assertEqual(self.page.topic_title.cget("text"), TOPICS[1].title)

    def test_up_arrow_from_first_topic_shows_last(self):
        self.press("Up")

        self.assertEqual(self.page.topic_title.cget("text"), TOPICS[-1].title)

    def test_chosen_topic_is_remembered(self):
        self.press("Down")

        self.assertEqual(self.app.settings.get("grammar_index"), 1)


class TopicListTests(GrammarTestCase):
    def test_topics_are_grouped_under_section_labels(self):
        """В оглавлении над темами стоят подписи разделов: ОСНОВЫ, ВРЕМЕНА..."""
        sections = list(dict.fromkeys(topic.section.upper() for topic in TOPICS))

        shown = [label.cget("text") for label in self.page.section_labels]

        self.assertEqual(shown, sections)

    def test_list_scrolls_to_current_topic(self):
        """Тем много, список прокручивается. Стрелкой с первой темы - на последнюю,
        и её кнопка должна оказаться в видимой части списка."""
        self.press("Up")
        self.app.update()

        button = self.page.topic_buttons[-1]
        top, bottom = self.page.topic_list._parent_canvas.yview()
        height = self.page.topic_list.winfo_height()
        place = (button.winfo_y() + button.winfo_height() / 2) / height
        self.assertTrue(top <= place <= bottom, (top, place, bottom))


class TableTests(GrammarTestCase):
    def test_wide_table_fits_inside_card(self):
        """В таблице "Все 12 времён" 4 колонки с длинным текстом. Клетки должны
        переносить текст, а не уходить за правый край карточки."""
        self.app.geometry("1200x780")  # обычный размер окна на небольшом экране
        index = next(
            i for i, topic in enumerate(TOPICS) if topic.title == "Все 12 времён"
        )
        self.page.show(index)
        self.app.update()

        visible = self.page.scroll._parent_canvas.winfo_width()  # видимая часть
        # reqwidth - сколько места таблица просит. Если больше видимого, её обрежут.
        widest = max(cell.master.winfo_reqwidth() for cell in self.page.cells)
        self.assertLessEqual(widest, visible)

    def test_every_cell_of_topic_is_on_screen(self):
        table = TOPICS[0].tables[0]

        shown = [cell.cget("text") for cell in self.page.cells]

        for row in table.rows:
            for text in row:
                self.assertIn(text, shown)

    def test_click_on_english_cell_speaks_it(self):
        """В первой таблице английский - в первой колонке: щелчок по "I" произносит "I"."""
        cell = next(cell for cell in self.page.cells if cell.cget("text") == "I")

        cell.event_generate("<Button-1>")

        self.assertEqual(self.spoken[-1], ("I", False))


if __name__ == "__main__":
    unittest.main()
