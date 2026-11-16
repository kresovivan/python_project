# Китайский: проверка ответа пиньинем (core/answers.py, PinyinChecker)
# и поиск слова по пиньиню (core/vocabulary.py).
#
# Пиньинь - запись китайского слова латинскими буквами: 电脑 - diànnǎo.
# Значки над гласными - тоны. На обычной клавиатуре их не набрать, поэтому
# ответ принимается без тонов: "diannao". Пробелы и цифры тонов (dian4nao3)
# тоже не мешают.

import unittest

from core.answers import PinyinChecker, strip_tones
from core.models import Word
from core.vocabulary import Vocabulary
from tests.support import ROOT


def word(hanzi: str, pinyin: str) -> Word:
    """Китайское слово: иероглифы, перевод, пиньинь, тема."""
    return Word(hanzi, "перевод", pinyin, "Тест")


COMPUTER = word("电脑", "diànnǎo")
GIRL = word("女孩", "nǚhái")


class StripTonesTests(unittest.TestCase):
    def test_tone_marks_are_removed(self):
        self.assertEqual(strip_tones("diànnǎo"), "diannao")

    def test_u_with_dots_becomes_plain_u(self):
        self.assertEqual(strip_tones("nǚ"), "nu")


class PinyinCheckerTests(unittest.TestCase):
    def test_pinyin_without_tones_is_correct(self):
        self.assertTrue(PinyinChecker.is_correct("diannao", COMPUTER))

    def test_spaces_and_case_are_ignored(self):
        self.assertTrue(PinyinChecker.is_correct("Dian Nao", COMPUTER))

    def test_tone_numbers_are_ignored(self):
        self.assertTrue(PinyinChecker.is_correct("dian4nao3", COMPUTER))

    def test_v_can_be_typed_instead_of_u_with_dots(self):
        """На клавиатуре нет буквы ü, вместо неё по традиции пишут v: nvhai."""
        self.assertTrue(PinyinChecker.is_correct("nvhai", GIRL))

    def test_other_word_is_wrong(self):
        self.assertFalse(PinyinChecker.is_correct("dianshi", COMPUTER))

    def test_hieroglyphs_are_not_the_expected_answer(self):
        """Вводится пиньинь, а не иероглифы: их без китайской раскладки не набрать."""
        self.assertEqual(PinyinChecker.expected(COMPUTER), "diannao")

    def test_hint_does_not_give_away_pinyin(self):
        """В подсказке первая буква и иероглифы, но не сам пиньинь с тонами."""
        hint = PinyinChecker.hint_text(COMPUTER)

        self.assertTrue(hint.startswith("d _"))
        self.assertIn("电脑", hint)
        self.assertNotIn("diànnǎo", hint)


class SearchByPinyinTests(unittest.TestCase):
    def test_word_is_found_by_pinyin_without_tones(self):
        vocabulary = Vocabulary([COMPUTER, GIRL], sound_key=PinyinChecker.normalize)

        found = vocabulary.search("diannao")

        self.assertEqual(found, [COMPUTER])

    def test_english_dictionary_does_not_search_pronunciation(self):
        """В английском словаре произношение записано русскими буквами:
        поиск по нему находил бы лишнее (запрос "лу" нашёл бы loop - "луп")."""
        loop = Word("loop", "цикл", "луп", "Тест")
        vocabulary = Vocabulary([loop])

        self.assertEqual(vocabulary.search("луп"), [])


class ChineseDictionaryTests(unittest.TestCase):
    """Настоящие файлы data/zh/: заполнены без ошибок."""

    FOLDER = ROOT / "data" / "zh"

    def test_every_word_has_pinyin_without_tones_to_type(self):
        vocabulary = Vocabulary.from_folder(self.FOLDER)

        empty = [w.en for w in vocabulary.all_words() if not PinyinChecker.expected(w)]

        self.assertEqual(empty, [])

    def test_no_word_is_written_twice(self):
        """Словарь оставляет только первое из одинаковых слов, второе молча
        пропадает. 只 (zhǐ, "только") и 只 (zhī, счётное слово) пишутся
        одинаково - такие значения нужно объединять в одну строку."""
        written = []
        for path in self.FOLDER.glob("*.txt"):
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip() and not line.startswith("#"):
                    written.append(line.split("|")[0])

        repeated = sorted({word for word in written if written.count(word) > 1})

        self.assertEqual(repeated, [])


if __name__ == "__main__":
    unittest.main()
