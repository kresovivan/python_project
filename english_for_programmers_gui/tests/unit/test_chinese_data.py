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

import re
import unicodedata
import unittest
from functools import lru_cache

from core import grammar_zh, pinyin
from tests.support import ROOT

INITIALS = "b p m f d t n l g k h j q x zh ch sh r z c s".split()
# Слоги без начального звука и особые случаи (y, w, zhi, ri ...).
SPECIAL = """a ai an ang ao e ei en eng er o ou
zhi chi shi ri zi ci si
ya yan yang yao ye yi yin ying yo yong you yu yuan yue yun
wa wai wan wang wei wen weng wo wu""".split()
# Окончания, которые встречаются после начальных звуков. ü записано как v.
FINALS = """a ai an ang ao e ei en eng o ong ou
i ia ian iang iao ie in ing iong iu
u ua uai uan uang ui un uo v ve van vn ue uan un""".split()
# Сочетания, которых в путунхуа нет, хотя по таблице они складываются.
# Проверка не обязана их запрещать: главное - ловить опечатки вроде "xqa".
SYLLABLES = set(SPECIAL) | {i + f for i in INITIALS for f in FINALS}

TONE_MARKS = "āáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜ"
LATIN_WORDS = {"python", "java", "windows", "linux", "c", "go"}  # не пиньинь


def plain(text: str) -> str:
    """Без тонов, ü как v, строчными: "Nǚ" превращается в "nv"."""
    text = unicodedata.normalize("NFC", text).lower().replace("ü", "v")
    text = "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")
    return unicodedata.normalize("NFC", text).replace("ü", "v")


def split_syllables(word: str) -> list[str] | None:
    """Разбить слово пиньиня без пробелов на слоги с тонами (None - не разбивается).

    Берём разбиение на наименьшее число слогов: "xian" - один слог, а не xi + an.
    Буква r в конце после гласной - это "эризация" (zhèr), отдельным слогом не считаем.
    """
    toned = unicodedata.normalize("NFC", word).lower().replace("ü", "v")
    bare = plain(word)
    if len(toned) != len(bare):  # редкий случай необычной записи - сверяем по bare
        toned = bare

    @lru_cache(None)
    def best(start: int) -> tuple | None:
        if start == len(bare):
            return ()
        options = []
        for end in range(start + 1, min(start + 6, len(bare)) + 1):
            rest = best(end)
            if bare[start:end] in SYLLABLES and rest is not None:
                options.append(((start, end), *rest))
        return min(options, key=len) if options else None

    if bare.endswith("r") and best(0) is None and len(bare) > 1:
        cut = split_syllables(word[:-1])
        return cut
    parts = best(0)
    return None if parts is None else [toned[a:b] for a, b in parts]


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
        for part in re.split(r"['’]", word):
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
