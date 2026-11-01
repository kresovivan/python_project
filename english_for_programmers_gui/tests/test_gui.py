import ctypes
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import customtkinter as ctk

from core import speech
from core.lesson import WEAK_WORDS
from core.progress import NEW
from gui.app import App
from tests.support import ROOT, close_app, copy_resources, event, pump, send_wm_close, titled_windows, wait_for_new_window


class GuiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="efp_gui_tests_")
        root = Path(self.tmp.name)
        self.base = root / "resources"
        self.base.mkdir()
        shutil.copytree(ROOT / "data", self.base / "data")
        shutil.copytree(ROOT / "assets", self.base / "assets")
        self.user_data = root / "user_data"
        self._edge_tts = speech.edge_tts
        speech.edge_tts = None
        self.app = self._create_app()
        self.spoken = []
        self.app.voice.say = lambda text, slow=False: self.spoken.append((text, slow))
        self.app.voice.prefetch = lambda text: None

    def tearDown(self):
        try:
            if self.app is not None:
                close_app(self.app)
        finally:
            speech.edge_tts = self._edge_tts
            self.tmp.cleanup()

    def _create_app(self):
        app = App(self.base, self.user_data)
        pump(app, 0.2)
        return app

    def test_navigation_hotkeys_help_and_themes(self):
        app = self.app
        self.assertEqual(app.current.key, "home")
        self.assertEqual(len(app.pages), 7)
        self.assertEqual(sum(page.winfo_ismapped() for page in app.pages.values()), 1)
        for number, key in enumerate(app.host.keys, 1):
            app._on_key(event(str(number), 48 + number, 0x0004))
            pump(app)
            self.assertEqual(app.current.key, key)
        app._on_key(event("Tab", 9, 0x0004))
        self.assertEqual(app.current.key, "home")
        app._on_key(event("ISO_Left_Tab", 9, 0x0005))
        self.assertEqual(app.current.key, "stats")
        app._on_key(event("F1"))
        self.assertTrue(app.help.visible)
        app._on_key(event("2", 50, 0x0004))
        self.assertTrue(app.help.visible)
        self.assertEqual(app.current.key, "stats")
        app._on_key(event("Escape"))
        self.assertFalse(app.help.visible)
        app._on_key(event("е", 84, 0x0004))
        pump(app)
        self.assertEqual(ctk.get_appearance_mode(), "Light")
        app._on_key(event("е", 84, 0x0004))
        self.assertEqual(ctk.get_appearance_mode(), "Dark")
        for digit, key in enumerate(("cards", "choice", "typing", "errors"), 1):
            app.show_page("home")
            app._on_key(event(str(digit)))
            self.assertEqual(app.current.key, key)

    def test_cards_choice_and_typing_flow(self):
        app = self.app
        cards = app.pages["cards"]
        app.show_page("cards")
        app._on_key(event("т", 78, 0x0004))
        self.assertIs(cards._screen, cards.body)
        self.assertEqual(cards.session.index, 0)
        first_card = cards.word
        app._on_key(event("2"))
        self.assertEqual(cards.session.index, 0)
        app._on_key(event("space"))
        self.assertTrue(cards.revealed)
        self.assertEqual(cards.ru_label.cget("text"), first_card.ru)
        app._on_key(event("2"))
        self.assertEqual(cards.session.index, 1)
        self.assertEqual(cards.session.right, 1)
        self.assertEqual(app.settings.session("cards").index, 1)
        self.assertNotEqual(cards.word, first_card)
        old_topic = cards.topic_menu.get()
        app._on_key(event("Down", 40, 0x0004))
        self.assertNotEqual(cards.topic_menu.get(), old_topic)

        choice = app.pages["choice"]
        app.show_page("choice")
        choice.start_new()
        self.assertEqual(len(choice.options), 4)
        self.assertIn(choice.word.ru, choice.options)
        correct = choice.options.index(choice.word.ru)
        wrong = next(i for i in range(4) if i != correct and choice.options[i] != choice.word.ru)
        choice.choose(wrong)
        self.assertTrue(choice.answered)
        self.assertEqual(choice.session.wrong, 1)
        answered_word = choice.word
        choice.choose(correct)
        self.assertEqual(choice.session.answered, 1)
        self.assertTrue(all(str(button.cget("state")) == "disabled" for button in choice.option_buttons))
        app._on_key(event("Return"))
        self.assertNotEqual(choice.word, answered_word)
        correct = choice.options.index(choice.word.ru)
        answered_word = choice.word
        choice.choose(correct)
        self.assertEqual(choice.session.right, 1)
        pump(app, 1.0)
        self.assertNotEqual(choice.word, answered_word)

        typing = app.pages["typing"]
        app.show_page("typing")
        typing.start_new()
        self.assertIsNone(typing.speak_text())
        app._on_key(event("р", 72, 0x0004))
        self.assertTrue(typing.feedback.cget("text"))
        self.assertEqual(str(typing.hint_button.cget("state")), "disabled")
        typing.entry.insert(0, "   ")
        typing.submit()
        self.assertFalse(typing.answered)
        typing.entry.delete(0, "end")
        typing.entry.insert(0, "definitely wrong answer")
        app._on_key(event("Return"))
        self.assertTrue(typing.answered)
        self.assertEqual(typing.session.wrong, 1)
        self.assertEqual(typing.speak_text(), typing.word.answer)
        self.assertEqual(str(typing.entry.cget("state")), "disabled")
        app._on_key(event("з", 80))
        self.assertEqual(self.spoken[-1], (typing.word.answer, False))
        app._on_key(event("з", 80, 0x0001))
        self.assertEqual(self.spoken[-1], (typing.word.answer, True))
        app._on_key(event("Return"))
        self.assertFalse(typing.answered)
        self.assertEqual(typing.session.index, 1)
        typing.entry.insert(0, typing.word.answer.upper().replace(" ", "  ") + "!")
        typing.submit()
        self.assertEqual(typing.session.right, 1)
        typing.submit()
        self.assertEqual(typing.session.index, 2)

    def test_errors_dictionary_stats_and_reset(self):
        app = self.app
        errors = app.pages["errors"]
        app.show_page("errors")
        app._on_key(event("space"))
        self.assertTrue(errors.revealed)
        self.assertTrue(errors.rows["ru"].cget("text"))
        errors.index = len(errors.errors) - 1
        app._on_key(event("Right"))
        self.assertEqual(errors.index, 0)
        app._on_key(event("Left"))
        self.assertEqual(errors.index, len(errors.errors) - 1)
        self.assertEqual(app.settings.get("errors_index"), errors.index)
        self.assertEqual(errors.speak_text(), errors.errors[errors.index].message)

        dictionary = app.pages["dictionary"]
        app.show_page("dictionary")
        pump(app)
        dictionary.query.insert(0, "LOOP")
        dictionary.search()
        self.assertIn("НАЙДЕНО", dictionary.info.cget("text"))
        self.assertIn("loop", dictionary.results.text.get("1.0", "end").lower())
        text_widget = dictionary.results.text
        binding = text_widget.tk.call(text_widget._w, "tag", "bind", dictionary._speak_tags[0], "<Button-1>")
        self.assertTrue(binding)
        before = len(self.spoken)
        app._on_key(event("з", 80))
        self.assertEqual(len(self.spoken), before)
        app._on_key(event("Escape"))
        self.assertEqual(app.current.key, "dictionary")
        self.assertFalse(dictionary.query.get())
        dictionary.query.insert(0, "перемен")
        dictionary.search()
        self.assertIn("НАЙДЕНО", dictionary.info.cget("text"))
        app._on_key(event("Escape"))
        app._on_key(event("Escape"))
        self.assertEqual(app.current.key, "home")
        app._on_key(event("а", 70, 0x0004))
        self.assertEqual(app.current.key, "dictionary")

        stats = app.pages["stats"]
        app.show_page("stats")
        pump(app)
        self.assertEqual(len(stats.topic_bars.rows), 18)
        self.assertTrue(stats.chart.find_all())
        self.assertIn("Выучено", stats.total_label.cget("text"))
        before = app.progress.today_total()
        with patch("gui.pages.stats.messagebox.askyesno", return_value=False):
            stats.reset()
        self.assertEqual(app.progress.today_total(), before)
        with patch("gui.pages.stats.messagebox.askyesno", return_value=True):
            stats.reset()
        self.assertEqual(app.progress.today_total(), 0)
        self.assertEqual(app.progress.counts(app.vocabulary.all_words())[NEW], 3621)

    def test_empty_weak_words(self):
        cards = self.app.pages["cards"]
        self.app.show_page("cards")
        cards.topic_menu.set(WEAK_WORDS)
        cards.start_new()
        self.assertIs(cards._screen, cards.intro)
        self.assertIn("Слабых слов", cards.intro_label.cget("text"))

    def test_session_restored_after_recreating_application(self):
        first = self.app
        typing = first.pages["typing"]
        first.show_page("typing")
        typing.start_new()
        typing.entry.insert(0, "wrong")
        typing.submit()
        saved = first.settings.session("typing")
        expected_key = saved.keys[saved.index]
        first.show_page("home")
        self.assertTrue(first.pages["home"].hero_button.cget("text").startswith("Продолжить"))
        close_app(first)
        self.app = None

        second = self._create_app()
        self.app = second
        second.voice.say = lambda text, slow=False: None
        second.voice.prefetch = lambda text: None
        second._on_key(event("Return"))
        pump(second)
        self.assertEqual(second.current.key, "typing")
        self.assertEqual(second.pages["typing"].word.en, expected_key)

    def test_chart_date_labels_fit_inside_canvas(self):
        stats = self.app.pages["stats"]
        self.app.show_page("stats")
        pump(self.app, 0.25)
        canvas = stats.chart
        labels = [
            item
            for item in canvas.find_all()
            if canvas.type(item) == "text" and canvas.itemcget(item, "text").isdigit()
        ]
        self.assertEqual(len(labels), 14)
        overflow = [canvas.bbox(item) for item in labels if canvas.bbox(item)[3] > canvas.winfo_height()]
        self.assertFalse(overflow, f"Подписи дат выходят за холст: {overflow}")


@unittest.skipUnless(sys.platform == "win32", "WM_CLOSE проверяется в Windows")
class MainProcessTests(unittest.TestCase):
    def test_main_process_opens_and_closes_without_errors(self):
        with tempfile.TemporaryDirectory(prefix="efp_main_process_") as tmp:
            root = Path(tmp)
            copy_resources(root)
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
            previous = set(titled_windows())
            process = subprocess.Popen(
                [sys.executable, str(root / "main.py")],
                cwd=root,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            try:
                hwnd = wait_for_new_window(previous, process)
                time.sleep(0.5)
                send_wm_close(hwnd)
                process.wait(timeout=12)
                out, err = process.communicate(timeout=2)
                self.assertEqual(process.returncode, 0, (out, err))
                self.assertFalse(err.strip(), err)
                state = json.loads((root / "user_data" / "state.json").read_text(encoding="utf-8"))
                self.assertTrue(state.get("window", {}).get("geometry"))
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()


if __name__ == "__main__":
    unittest.main()
