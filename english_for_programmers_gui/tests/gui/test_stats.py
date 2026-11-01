# Страница "Прогресс": общий итог, график за 14 дней, прогресс по темам, сброс.

import unittest
from unittest.mock import patch

from core.progress import NEW
from tests.gui.base import GuiTestCase
from tests.support import pump


class StatsTestCase(GuiTestCase):
    def setUp(self):
        super().setUp()
        self.page = self.open_page("stats")

    def answer_some_word(self) -> None:
        word = self.app.vocabulary.all_words()[0]
        self.app.progress.record(word, True)
        self.page.on_show()


class SummaryTests(StatsTestCase):
    def test_every_topic_has_progress_bar(self):
        self.assertEqual(
            len(self.page.topic_bars.rows), len(self.app.vocabulary.topics())
        )

    def test_total_learned_is_shown(self):
        self.assertIn("Выучено", self.page.total_label.cget("text"))


class ChartTests(StatsTestCase):
    def date_labels(self) -> list[int]:
        canvas = self.page.chart
        pump(self.app, 0.2)
        return [
            item
            for item in canvas.find_all()
            if canvas.type(item) == "text" and canvas.itemcget(item, "text").isdigit()
        ]

    def test_chart_has_label_for_each_of_14_days(self):
        self.assertEqual(len(self.date_labels()), 14)

    def test_date_labels_fit_inside_chart(self):
        """Ошибка, найденная тестом: при масштабе 200% даты обрезались снизу."""
        canvas = self.page.chart
        labels = self.date_labels()

        outside = [
            canvas.bbox(item)
            for item in labels
            if canvas.bbox(item)[3] > canvas.winfo_height()
        ]

        self.assertEqual(outside, [])


class ResetTests(StatsTestCase):
    def test_cancelled_reset_keeps_progress(self):
        self.answer_some_word()

        with patch("gui.pages.stats.messagebox.askyesno", return_value=False):
            self.page.reset()

        self.assertEqual(self.app.progress.today_total(), 1)

    def test_confirmed_reset_makes_all_words_new(self):
        self.answer_some_word()

        with patch("gui.pages.stats.messagebox.askyesno", return_value=True):
            self.page.reset()

        words = self.app.vocabulary.all_words()
        self.assertEqual(self.app.progress.counts(words)[NEW], len(words))


if __name__ == "__main__":
    unittest.main()
