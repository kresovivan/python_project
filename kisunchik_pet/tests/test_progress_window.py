# -*- coding: utf-8 -*-
"""Тест окна прогресса: адаптивная вёрстка без наложений.

Проверяем на живом tkinter, что строки блоков не наезжают друг на
друга (каждая следующая строка начинается ниже конца предыдущей),
окно не уже содержимого, а график недели помещается в свою канву.
Именно наложение строк было главной жалобой на масштабе 200%.
"""

import json
import tempfile
import tkinter as tk
import unittest
from pathlib import Path

from core.progress import ProgressStore
from core.tutor import EnglishTutor
from gui.progress_window import ProgressWindow

ASSETS = Path(__file__).resolve().parent.parent / "assets"


def row_spans(rows_frame):
    """Вертикальные интервалы (y0, y1) каждой grid-строки."""
    rows = {}
    for child in rows_frame.winfo_children():
        info = child.grid_info()
        r = int(info["row"])
        y0 = child.winfo_y()
        y1 = y0 + child.winfo_reqheight()
        span = rows.get(r, (y0, y1))
        rows[r] = (min(span[0], y0), max(span[1], y1))
    return [rows[k] for k in sorted(rows)]


class TestProgressWindowLayout(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def _make_window(self, tmp):
        progress = ProgressStore(
            Path(tmp) / "progress.json",
            today=lambda: "2026-11-21")
        progress.mark_shown("cat")
        progress.mark_said("cat")
        tutor = EnglishTutor(ASSETS / "words.json",
                             ASSETS / "categories.json",
                             progress=progress)
        win = ProgressWindow(self.root, tutor, progress)
        win.win.update()
        return win

    def test_rows_do_not_overlap(self):
        """Строки блоков идут одна под другой без наложений."""
        with tempfile.TemporaryDirectory() as tmp:
            win = self._make_window(tmp)
            try:
                spans = row_spans(win.rows)
                self.assertGreater(len(spans), 20)  # все блоки нарисованы
                for prev, nxt in zip(spans, spans[1:]):
                    self.assertLessEqual(
                        prev[1], nxt[0] + 1,
                        f"строки наложились: {prev} и {nxt}")
            finally:
                win.close()

    def test_window_not_narrower_than_content(self):
        """Окно само достаточно широкое: minsize покрывает список."""
        with tempfile.TemporaryDirectory() as tmp:
            win = self._make_window(tmp)
            try:
                need = win.rows.winfo_reqwidth()
                min_w = win.win.minsize()[0]
                self.assertGreaterEqual(min_w, need,
                                        "minsize меньше содержимого")
            finally:
                win.close()

    def test_week_chart_fits_canvas(self):
        """Все элементы графика недели видимы внутри канвы."""
        with tempfile.TemporaryDirectory() as tmp:
            win = self._make_window(tmp)
            try:
                c = win.week_canvas
                bbox = c.bbox("all")
                self.assertIsNotNone(bbox)
                self.assertGreaterEqual(bbox[1], 0)
                self.assertLessEqual(bbox[3], c.winfo_reqheight())
            finally:
                win.close()

    def test_counts_visible_for_every_category(self):
        """У каждого блока есть цифры прогресса и кнопка "заново"."""
        with tempfile.TemporaryDirectory() as tmp:
            win = self._make_window(tmp)
            try:
                labels = [c for c in win.rows.winfo_children()
                          if isinstance(c, tk.Label)]
                texts = [c.cget("text") for c in labels]
                counts = [t for t in texts if "/" in t and "%" in t]
                agains = [t for t in texts if t == "заново"]
                # 21 блок: у каждого цифры и кнопка сброса.
                self.assertEqual(len(counts), 21)
                self.assertEqual(len(agains), 21)
            finally:
                win.close()


if __name__ == "__main__":
    unittest.main()
