# Страница "Написание слова": русский перевод, пользователь пишет слово по-английски.

import unittest

from tests.gui.base import GuiTestCase

H_KEY, P_KEY = 72, 80  # Ctrl+H - подсказка, P - произнести (русские "р" и "з")


class TypingTestCase(GuiTestCase):
    def setUp(self):
        super().setUp()
        self.page = self.open_page("typing")
        self.page.start_new()

    def type_answer(self, text: str) -> None:
        self.page.entry.delete(0, "end")
        self.page.entry.insert(0, text)
        self.press("Return")


class CheckTests(TypingTestCase):
    def test_empty_answer_is_not_accepted(self):
        self.type_answer("   ")

        self.assertFalse(self.page.answered)
        self.assertEqual(self.page.session.answered, 0)

    def test_wrong_answer_is_counted_as_mistake(self):
        self.type_answer("definitely wrong answer")

        self.assertEqual(self.page.session.wrong, 1)

    def test_answer_ignores_case_extra_spaces_and_punctuation(self):
        answer = self.page.word.answer.upper().replace(" ", "  ") + "!"

        self.type_answer(answer)

        self.assertEqual(self.page.session.right, 1)

    def test_input_is_locked_after_answer(self):
        self.type_answer("wrong")

        self.assertEqual(str(self.page.entry.cget("state")), "disabled")

    def test_enter_after_answer_shows_next_word(self):
        first = self.page.word
        self.type_answer("wrong")

        self.press("Return")

        self.assertFalse(self.page.answered)
        self.assertNotEqual(self.page.word, first)


class HintTests(TypingTestCase):
    def test_ctrl_h_shows_hint_in_russian_layout(self):
        self.press("р", H_KEY, ctrl=True)

        self.assertTrue(self.page.feedback.cget("text"))

    def test_hint_can_be_taken_only_once(self):
        self.press("р", H_KEY, ctrl=True)

        self.assertEqual(str(self.page.hint_button.cget("state")), "disabled")


class SpeakTests(TypingTestCase):
    def test_word_is_not_spoken_before_answer(self):
        """Произношение до ответа - это подсказка, его быть не должно."""
        self.assertIsNone(self.page.speak_text())

    def test_p_after_answer_speaks_word(self):
        self.type_answer("wrong")

        self.press("з", P_KEY)

        self.assertEqual(self.spoken[-1], (self.page.word.answer, False))

    def test_shift_p_speaks_word_slowly(self):
        self.type_answer("wrong")

        self.press("З", P_KEY, shift=True)

        self.assertEqual(self.spoken[-1], (self.page.word.answer, True))


if __name__ == "__main__":
    unittest.main()
