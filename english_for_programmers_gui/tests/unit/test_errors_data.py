# Сообщения об ошибках Python для режима "Читаем ошибки" (core/errors_data.py).

import re
import unittest

from core.errors_data import ERRORS


class ErrorsDataTests(unittest.TestCase):
    def test_there_are_errors_to_learn(self):
        self.assertTrue(ERRORS)

    def test_every_error_has_translation_word_breakdown_and_hint(self):
        empty = [
            error.message
            for error in ERRORS
            if not (error.ru and error.words and error.hint)
        ]

        self.assertEqual(empty, [])

    def test_every_message_looks_like_real_python_error(self):
        """Как в терминале: "NameError: name 'eggs' is not defined"."""
        pattern = re.compile(r"[A-Z]\w*(Error|Warning): .+")
        wrong = [
            error.message for error in ERRORS if not pattern.fullmatch(error.message)
        ]

        self.assertEqual(wrong, [])

    def test_messages_are_not_repeated(self):
        messages = [error.message for error in ERRORS]

        self.assertEqual(len(messages), len(set(messages)))


if __name__ == "__main__":
    unittest.main()
