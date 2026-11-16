# =============================================================================
# ПРОВЕРКА ОТВЕТОВ - сравнение введённого слова с правильным и подсказка
# =============================================================================
#
# Что это в жизни: "учитель, который проверяет диктант". Он сравнивает то,
# что написал ученик, с правильным словом и не придирается к мелочам:
# регистру букв, знакам препинания, лишним пробелам. Если ученик застрял,
# даёт подсказку: первую букву и прочерки вместо остальных.
#
# Два учителя - для двух языков (наследование):
#   AnswerChecker  - английский: ученик пишет само слово;
#   PinyinChecker  - китайский: ученик пишет пиньинь (запись латиницей) без тонов.
# Какой учитель нужен, знает язык (core/language.py, Language.checker).
#
# Логика без интерфейса: её можно проверять и менять, не открывая окно.
# Кто пользуется: страница "Написание слова" (gui/pages/study.py, TypingPage).
# Тесты: tests/unit/test_answer_checker.py, tests/unit/test_pinyin.py.

import unicodedata

from core.models import Word


def strip_tones(text: str) -> str:
    """Убрать значки тонов: "diànnǎo" превращается в "diannao", "nǚ" - в "nu".

    Буква с тоном в Юникоде может храниться как две части: обычная буква
    и "надстрочный значок" (по-английски combining mark). Нормализация NFD
    разбирает букву на эти части, а потом значки (категория "Mn") выбрасываем.
    """
    parts = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in parts if unicodedata.category(ch) != "Mn")


class AnswerChecker:
    """Правила проверки ответа в режиме "Написание слова"."""

    # Символы, которые не учитываются при сравнении. ’ - типографский апостроф.
    IGNORED = "!?.,'’`\""

    @classmethod
    def normalize(cls, text: str) -> str:
        """Например, "It Doesn't work!" превращается в "it doesnt work".

        @classmethod - метод получает класс (cls), а не объект: так он
        может прочитать константу IGNORED и у наследника, если её поменяют.
        """
        text = text.lower().strip()
        for ch in cls.IGNORED:
            text = text.replace(ch, "")
        return " ".join(text.split())

    @classmethod
    def expected(cls, word: Word) -> str:
        """Что ученик должен ввести. У английского - само слово без пояснения."""
        return word.answer

    @classmethod
    def is_correct(cls, typed: str, word: Word) -> bool:
        return cls.normalize(typed) == cls.normalize(cls.expected(word))

    @classmethod
    def hint_text(cls, word: Word) -> str:
        """Подсказка на экране: прочерки и произношение русскими буквами."""
        return f"{cls.hint(cls.expected(word))}    [ {word.sound} ]"

    @staticmethod
    def hint(text: str) -> str:
        """Первая буква, вместо остальных - прочерки. "Can you" -> "C _ _   _ _ _"."""
        result = text[0]
        for ch in text[1:]:
            if ch == " ":
                result += "   "
            elif ch.isalpha():
                result += " _"
            else:
                result += " " + ch
        return result


class PinyinChecker(AnswerChecker):
    """Китайский: ученик видит перевод и пишет пиньинь без тонов.

    Наследник AnswerChecker: метод hint (прочерки) достался от родителя,
    а правила "что ввести" и "что не важно" здесь свои (переопределены).
    """

    @classmethod
    def normalize(cls, text: str) -> str:
        """Например, "Dian4 Nao3" и "diànnǎo" оба превращаются в "diannao".

        Не важны: регистр, тоны (значки или цифры 1-5), пробелы, апострофы
        (xi'an), дефисы. Буква ü пишется на клавиатуре как v или как u.
        """
        text = strip_tones(text.lower()).replace("v", "u")
        return "".join(ch for ch in text if ch.isalpha() and ch.isascii())

    @classmethod
    def expected(cls, word: Word) -> str:
        """Пиньинь слова без тонов: для 电脑 (diànnǎo) - "diannao"."""
        return cls.normalize(word.sound)

    @classmethod
    def hint_text(cls, word: Word) -> str:
        """Первая буква пиньиня и иероглифы. Сам пиньинь не показываем: это и есть ответ."""
        return f"{cls.hint(cls.expected(word))}    {word.answer}"
