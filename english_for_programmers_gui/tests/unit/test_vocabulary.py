# Словарь (core/vocabulary.py): загрузка файлов data/*.txt, поиск,
# неправильные варианты для "Выбора перевода".
#
# Почти все тесты используют маленький словарь, написанный прямо в тесте.
# Настоящий словарь проверяется отдельно, в классе RealDictionaryTests.

import tempfile
import unittest
from pathlib import Path

from core.vocabulary import Vocabulary
from tests.support import DATA, use_fixed_random, write_vocabulary


class VocabularyTestCase(unittest.TestCase):
    def setUp(self):
        use_fixed_random(self)
        tmp = tempfile.TemporaryDirectory(prefix="efp_vocabulary_")
        self.addCleanup(tmp.cleanup)
        self.folder = Path(tmp.name)

    def load(self, text: str) -> Vocabulary:
        return write_vocabulary(self.folder, text)


class LoadingTests(VocabularyTestCase):
    def test_word_gets_translation_and_pronunciation(self):
        vocabulary = self.load("loop|цикл|луп")

        word = vocabulary.get("loop")

        self.assertEqual((word.ru, word.sound), ("цикл", "луп"))

    def test_word_belongs_to_topic_from_topic_line(self):
        vocabulary = self.load(
            """
            # topic: Циклы
            loop|цикл|луп
            """
        )

        self.assertEqual(vocabulary.get("loop").topic, "Циклы")

    def test_topic_is_file_name_when_there_is_no_topic_line(self):
        vocabulary = self.load("loop|цикл|луп")

        self.assertEqual(vocabulary.topics(), ["01"])

    def test_example_is_optional_fourth_field(self):
        vocabulary = self.load(
            """
            print|печатать|принт|print("Hi")
            loop|цикл|луп
            """
        )

        self.assertEqual(vocabulary.get("print").example, 'print("Hi")')
        self.assertEqual(vocabulary.get("loop").example, "")

    def test_comments_and_empty_lines_are_skipped(self):
        vocabulary = self.load(
            """
            # просто комментарий

            loop|цикл|луп
            """
        )

        self.assertEqual(len(vocabulary), 1)

    def test_repeated_word_is_loaded_once(self):
        """Слова "check" и "check (text)" - одно слово: в ответе пишут одно и то же."""
        vocabulary = self.load(
            """
            check|проверить|чек
            Check (text)|сверить|чек
            """
        )

        self.assertEqual(len(vocabulary), 1)
        self.assertEqual(vocabulary.get("check").ru, "проверить")

    def test_line_with_too_few_fields_is_reported_with_file_and_line(self):
        with self.assertRaisesRegex(ValueError, r"01\.txt, строка 2"):
            self.load(
                """
                loop|цикл|луп
                broken line
                """
            )


class QuestionsTests(VocabularyTestCase):
    def test_unknown_word_is_none(self):
        vocabulary = self.load("loop|цикл|луп")

        self.assertIsNone(vocabulary.get("lop"))

    def test_words_of_topic_cannot_be_spoiled_from_outside(self):
        """words() отдаёт копию списка: если её очистить, словарь не изменится."""
        vocabulary = self.load("loop|цикл|луп")

        vocabulary.words("01").clear()

        self.assertEqual(len(vocabulary.words("01")), 1)

    def test_search_finds_english_word_ignoring_case(self):
        vocabulary = self.load("loop|цикл|луп")

        found = vocabulary.search("LOOP")

        self.assertEqual([word.en for word in found], ["loop"])

    def test_search_finds_part_of_russian_translation_ignoring_case(self):
        vocabulary = self.load(
            """
            variable|переменная|вэриабл
            loop|цикл|луп
            """
        )

        found = vocabulary.search("ПЕРЕМЕН")

        self.assertEqual([word.en for word in found], ["variable"])


class DistractorsTests(VocabularyTestCase):
    """Неправильные варианты перевода для "Выбора перевода"."""

    TWO_TOPICS = """
        # topic: Циклы
        loop|цикл|луп
        break|прервать|брейк
        continue|продолжить|континью
        while|пока|вайл
        for|для|фо
        # topic: Git
        commit|фиксировать|коммит
        push|отправить|пуш
        pull|получить|пул
        merge|слить|мёрдж
        branch|ветка|бранч
    """

    def test_three_options_by_default(self):
        vocabulary = self.load(self.TWO_TOPICS)

        self.assertEqual(len(vocabulary.distractors(vocabulary.get("loop"))), 3)

    def test_options_never_contain_correct_translation(self):
        vocabulary = self.load(self.TWO_TOPICS)
        word = vocabulary.get("loop")

        for _ in range(30):
            self.assertNotIn("цикл", vocabulary.distractors(word))

    def test_options_come_from_same_topic(self):
        """Варианты из той же темы похожи на правильный - так тест полезнее."""
        vocabulary = self.load(self.TWO_TOPICS)
        loop_topic = {"прервать", "продолжить", "пока", "для"}

        for _ in range(30):
            self.assertLessEqual(
                set(vocabulary.distractors(vocabulary.get("loop"))), loop_topic
            )

    def test_small_topic_takes_options_from_whole_dictionary(self):
        vocabulary = self.load(
            """
            # topic: Маленькая
            loop|цикл|луп
            break|прервать|брейк
            # topic: Git
            commit|фиксировать|коммит
            push|отправить|пуш
            """
        )

        options = vocabulary.distractors(vocabulary.get("loop"))

        self.assertCountEqual(options, ["прервать", "фиксировать", "отправить"])

    def test_synonyms_do_not_give_same_option_twice(self):
        """Ошибка, найденная тестом: варианты повторялись.

        У синонимов одинаковый перевод: "shut down" и "turn off" - оба
        "выключить". Разных неправильных переводов здесь ровно три, значит,
        все три должны попасть в варианты, и каждый по одному разу.
        """
        vocabulary = self.load(
            """
            open|открыть|оупен
            shut down|выключить|шат даун
            turn off|выключить|тёрн офф
            restore|восстановить|ристор
            recover|восстановить|рикавер
            delete|удалить|дилит
            """
        )

        for _ in range(30):
            options = vocabulary.distractors(vocabulary.get("open"))
            self.assertCountEqual(options, ["выключить", "восстановить", "удалить"])


class RealDictionaryTests(unittest.TestCase):
    """Проверка настоящих файлов data/: в них нет ошибок заполнения.

    Количество слов здесь не проверяется: словарь пополняется, и тест
    не должен падать от того, что добавили новое слово.
    """

    @classmethod
    def setUpClass(cls):
        # Словарь читается один раз на все тесты класса: он только читается и не меняется.
        cls.vocabulary = Vocabulary(DATA)
        cls.words = cls.vocabulary.all_words()

    def test_dictionary_is_not_empty(self):
        self.assertTrue(self.words)

    def test_every_word_has_english_russian_and_pronunciation(self):
        empty = [
            word.en
            for word in self.words
            if not (word.en.strip() and word.ru.strip() and word.sound.strip())
        ]

        self.assertEqual(empty, [])

    def test_answers_are_unique(self):
        answers = [word.answer.casefold() for word in self.words]

        self.assertEqual(len(answers), len(set(answers)))

    def test_every_topic_has_words(self):
        empty = [
            topic
            for topic in self.vocabulary.topics()
            if not self.vocabulary.words(topic)
        ]

        self.assertEqual(empty, [])

    def test_every_word_gets_three_different_wrong_options(self):
        use_fixed_random(self)
        bad = []
        for word in self.words:
            options = self.vocabulary.distractors(word)
            if len(set(options)) != 3 or word.ru in options:
                bad.append((word.en, options))

        self.assertEqual(
            bad, [], f"Плохие варианты у {len(bad)} слов, например: {bad[:3]}"
        )


if __name__ == "__main__":
    unittest.main()
