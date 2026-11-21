# Китайские данные записаны без ошибок: словарь data/zh/, грамматика
# core/grammar_zh.py и "Звуки и тоны" core/pinyin.py.
#
# Что проверяется по каждой записи пиньиня:
#   1. каждый слог - настоящий слог путунхуа (их около 400, список ниже);
#   2. значок тона стоит над правильной гласной;
#   3. иероглифов столько же, сколько слогов (пропущенное слово видно сразу).
#
# Правило места значка тона (так пишут во всех учебниках):
#   если в слоге есть a или e - значок над ней (hǎo, xué);
#   иначе в сочетании ou - над o (kǒu);
#   иначе - над последней гласной (guì, liù, duō).
#
# Классы-помощники здесь же: это правила проверки данных, а не программы,
# поэтому им место в тестах, а не в core/.
#
# Списки слогов, разбиение на слоги и убирание тонов — в core/pinyin_utils.py
# (единый источник правды, чтобы не копировать между core/pinyin_ru.py и тестом).

import re
import unittest

from core import grammar_zh, pinyin
from core.pinyin_utils import bare as plain, split_syllables
from tests.support import ROOT

TONE_MARKS = "āáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜ"
LATIN_WORDS = {"python", "java", "windows", "linux", "c", "go"}  # не пиньинь


def tone_error(syllable: str) -> str | None:
    """Описание ошибки значка тона в слоге или None, если всё правильно."""
    marks = [c for c in syllable if c in TONE_MARKS]
    if len(marks) > 1:
        return "два значка тона"
    if not marks:
        return None  # лёгкий тон
    bare = plain(syllable)
    if "a" in bare:
        want = bare.index("a")
    elif "e" in bare:
        want = bare.index("e")
    elif "ou" in bare:
        want = bare.index("o")
    else:
        want = max(i for i, c in enumerate(bare) if c in "aeiouv")
    return None if syllable.index(marks[0]) == want else "значок не над той гласной"


def syllables_of(text: str) -> list[str] | None:
    """Все слоги записи пиньиня (фразы). Латинские слова вроде Python пропускаются."""
    result = []
    for word in re.split(r"[\s,.!?;:/\-]+", text):
        for part in re.split(r"['']", word):
            if not part or part.lower() in LATIN_WORDS:
                continue
            parts = split_syllables(part)
            if parts is None:
                return None
            result.extend(parts)
    return result


def syllable_count_matches(hanzi: str, syllables: list[str], text: str) -> bool:
    """Столько же слогов, сколько иероглифов?

    Исключение - 儿 в конце слова (эризация): 这儿 читается zhèr, одним слогом,
    и в пиньине на месте 儿 стоит только буква r. А в 儿子 (érzi) и 女儿 (nǚ'ér)
    儿 - полноценный слог ér.
    """
    total = len(re.findall(r"[一-鿿]", hanzi))
    if len(syllables) == total:
        return True
    # Эризация - буква r в конце слова: бывает после гласной (zhèr) и после
    # согласной (diǎnr, bǎngr), поэтому берём любую букву перед r.
    erhua = len(re.findall(r"[a-z]r\b", plain(text)))
    return "儿" in hanzi and len(syllables) == total - erhua


def all_records() -> list[tuple[str, str, str]]:
    """(откуда, иероглифы, пиньинь) из словаря и таблиц тетрадей."""
    records = []
    for path in sorted((ROOT / "data" / "zh").glob("*.txt")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.startswith("#"):
                fields = line.split("|")
                records.append((path.name, fields[0], fields[2]))
    for topic in grammar_zh.TOPICS + pinyin.TOPICS:
        for table in topic.tables:
            for row in table.rows:
                hanzi = [c for c in row if re.search(r"[一-鿿]", c)]
                latin = [c for c in row if any(m in c for m in TONE_MARKS) and not re.search(r"[一-鿿]", c)]
                # Строка таблицы "иероглифы | пиньинь | перевод": сверяем пару.
                if len(hanzi) == 1 and len(latin) == 1:
                    records.append((topic.title, hanzi[0], latin[0]))
    return records


class RulesTests(unittest.TestCase):
    """Сначала проверяем сами правила на заведомо верных и неверных примерах:
    тест, который ничего не ловит, бесполезен."""

    def test_correct_syllables_are_accepted(self):
        self.assertEqual(split_syllables("diànnǎo"), ["diàn", "nǎo"])
        self.assertEqual(split_syllables("nǚhái"), ["nǚ", "hái"])

    def test_typo_syllable_is_rejected(self):
        self.assertIsNone(split_syllables("xqa"))

    def test_erhua_r_is_not_a_separate_syllable(self):
        self.assertEqual(split_syllables("zhèr"), ["zhè"])

    def test_missing_word_in_pinyin_is_found(self):
        """Иероглифов три, а слогов два - в пиньине пропущено слово."""
        self.assertFalse(syllable_count_matches("我爱你", ["wǒ", "ài"], "wǒ ài"))

    def test_er_as_full_syllable_is_counted(self):
        """В 女儿 (дочь) 儿 - отдельный слог ér, а в 这儿 (здесь) - только буква r."""
        self.assertTrue(syllable_count_matches("女儿", ["nǚ", "ér"], "nǚ'ér"))
        self.assertTrue(syllable_count_matches("这儿", ["zhè"], "zhèr"))

    def test_erhua_after_consonant_is_counted(self):
        """点儿 читается diǎnr: r после согласной n - тоже эризация, не отдельный слог."""
        self.assertTrue(syllable_count_matches("有点儿", ["yǒu", "diǎn"], "yǒudiǎnr"))

    def test_tone_mark_in_right_place_is_accepted(self):
        for syllable in ("hǎo", "xué", "kǒu", "guì", "liù", "duō"):
            with self.subTest(syllable=syllable):
                self.assertIsNone(tone_error(syllable))

    def test_tone_mark_in_wrong_place_is_found(self):
        for syllable in ("haǒ", "xúe", "koǔ", "gùi"):
            with self.subTest(syllable=syllable):
                self.assertIsNotNone(tone_error(syllable))


class ChinesePinyinDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = all_records()

    def test_every_syllable_is_real(self):
        wrong = [(where, hz, py) for where, hz, py in self.records if syllables_of(py) is None]

        self.assertEqual(wrong, [])

    def test_tone_marks_are_in_right_place(self):
        wrong = [
            (where, hz, syllable)
            for where, hz, py in self.records
            for syllable in syllables_of(py) or []
            if tone_error(syllable)
        ]

        self.assertEqual(wrong, [])

    def test_as_many_syllables_as_hieroglyphs(self):
        """Иероглиф - это слог. Если чисел не совпадает, в пиньине пропущено
        или лишнее слово."""
        wrong = [
            (where, hz, py)
            for where, hz, py in self.records
            if syllables_of(py) is not None and not syllable_count_matches(hz, syllables_of(py), py)
        ]

        self.assertEqual(wrong, [])


if __name__ == "__main__":
    unittest.main()