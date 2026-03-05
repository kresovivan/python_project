"""
этот раздел полноправнео может считать модулем в Python
"""


def search4lvowels(phrase: str) -> set:
    """Возвращает гласные, найденные в указанной строке или фразе"""
    vowels = set("aeiou")
    return vowels.intersection(set(phrase))


def search4letters(phrase: str, letters: str = "aeiou") -> set:
    """Возвращает множество букв, найденных в указанной строке или фразе"""
    return set(letters).intersection(set(phrase))
