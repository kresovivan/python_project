def search4letters(phrase: str, letters: str = "aeiou") -> set:
    """Возвращает множество букв, найденных в указанной строке или фразе"""
    return set(letters).intersection(set(phrase))
