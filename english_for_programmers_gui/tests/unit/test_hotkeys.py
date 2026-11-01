# Распознавание клавиш (gui/hotkeys.py, класс KeyPress) - без окна.
#
# Самое хрупкое место программы: пользователь часто работает в русской
# раскладке. Ctrl+F в ней приходит как "Ctrl + а", и сочетание должно
# всё равно сработать. Поэтому буквы узнаются по номеру физической
# клавиши (keycode), а не по символу (keysym).

import unittest
from types import SimpleNamespace

from gui.hotkeys import HELP, KeyPress

CTRL, SHIFT = 0x0004, 0x0001
F_KEY = 70  # номер физической клавиши F (в русской раскладке на ней "а")


class LetterTests(unittest.TestCase):
    def test_letter_is_recognized_in_english_layout(self):
        self.assertTrue(KeyPress("f", F_KEY).is_letter("F"))

    def test_letter_is_recognized_in_russian_layout(self):
        self.assertTrue(KeyPress("а", F_KEY).is_letter("F"))

    def test_lowercase_letter_can_be_asked(self):
        self.assertTrue(KeyPress("а", F_KEY).is_letter("f"))

    def test_other_letter_is_not_recognized(self):
        self.assertFalse(KeyPress("а", F_KEY).is_letter("T"))


class ModifierTests(unittest.TestCase):
    def test_ctrl_is_recognized(self):
        self.assertTrue(KeyPress("а", F_KEY, CTRL).ctrl)

    def test_shift_is_recognized(self):
        self.assertTrue(KeyPress("P", 80, SHIFT).shift)

    def test_ctrl_and_shift_together(self):
        key = KeyPress("Tab", 9, CTRL | SHIFT)

        self.assertTrue(key.ctrl and key.shift)

    def test_no_modifiers(self):
        key = KeyPress("Return")

        self.assertFalse(key.ctrl or key.shift)


class NamedKeyTests(unittest.TestCase):
    def test_key_is_one_of_names(self):
        self.assertTrue(KeyPress("space").is_("Return", "space"))

    def test_key_is_not_one_of_names(self):
        self.assertFalse(KeyPress("Escape").is_("Return", "space"))

    def test_digit_key_gives_number(self):
        self.assertEqual(KeyPress("3").digit, 3)

    def test_non_digit_key_gives_no_number(self):
        self.assertIsNone(KeyPress("Return").digit)


class FromEventTests(unittest.TestCase):
    def test_key_press_is_made_from_tkinter_event(self):
        event = SimpleNamespace(keysym="а", keycode=F_KEY, state=CTRL)

        key = KeyPress.from_event(event)

        self.assertTrue(key.ctrl and key.is_letter("F"))

    def test_event_without_keycode_and_state_is_accepted(self):
        key = KeyPress.from_event(SimpleNamespace(keysym="Return"))

        self.assertEqual((key.code, key.state), (0, 0))


class HelpTests(unittest.TestCase):
    """Справка F1 строится из списка HELP: в нём не должно быть пустых строк."""

    def test_every_help_line_has_keys_and_action(self):
        empty = [
            (section, keys, action)
            for section, rows in HELP
            for keys, action in rows
            if not (keys and action)
        ]

        self.assertEqual(empty, [])


if __name__ == "__main__":
    unittest.main()
