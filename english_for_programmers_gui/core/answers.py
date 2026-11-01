# =============================================================================
# ПРОВЕРКА ОТВЕТОВ - сравнение введённого слова с правильным и подсказка
# =============================================================================
#
# Логика без интерфейса: её можно проверять и менять, не открывая окно.

from core.models import Word


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
    def is_correct(cls, typed: str, word: Word) -> bool:
        return cls.normalize(typed) == cls.normalize(word.answer)

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
