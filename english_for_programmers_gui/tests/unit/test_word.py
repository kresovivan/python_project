# Слово словаря (core/models.py, класс Word).
#
# Каждый тест устроен одинаково, по схеме "подготовка - действие - проверка"
# (по-английски Arrange - Act - Assert):
#   подготовка - создать нужные объекты;
#   действие   - сделать ОДНО действие, которое проверяем;
#   проверка   - убедиться, что результат такой, как требуется.
# Имя теста - это требование к программе, его можно прочитать как фразу.

import unittest

from core.models import Word


class WordAnswerTests(unittest.TestCase):
    """word.answer - то, что пользователь должен ввести в "Написании слова"."""

    def test_answer_drops_note_in_brackets(self):
        # подготовка
        word = Word("commit (DB)", "фиксировать", "коммит", "Базы данных")
        # действие
        answer = word.answer
        # проверка
        self.assertEqual(answer, "commit")

    def test_answer_without_note_is_the_word_itself(self):
        word = Word("loop", "цикл", "луп", "Циклы")

        self.assertEqual(word.answer, "loop")

    def test_answer_keeps_all_words_of_phrase(self):
        word = Word("pull request (GitHub)", "запрос на слияние", "пул риквест", "Git")

        self.assertEqual(word.answer, "pull request")


if __name__ == "__main__":
    unittest.main()
