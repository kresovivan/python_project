"""Компиляция и применение поискового шаблона."""

import re
from typing import Optional


class QueryCompiler:
    """Преобразует строку шаблона в скомпилированный regex.

    Синтаксис: ^ начало, $ конец, ? один символ, * любое число.
    Если шаблон пустой - возвращает None.
    """

    @staticmethod
    def compile(pattern: str) -> Optional[re.Pattern]:
        if not pattern:
            return None

        p = pattern.strip()
        anchored_start = p.startswith('^') and len(p) > 1
        anchored_end = p.endswith('$') and len(p) > 1

        if anchored_start:
            p = p[1:]
        if anchored_end:
            p = p[:-1]

        p = re.escape(p)
        p = p.replace(r'\?', '.').replace(r'\*', '.*')

        regex = (('^' if anchored_start else '') + p +
                 ('$' if anchored_end else ''))
        return re.compile(regex, re.IGNORECASE)


class QueryMatcher:
    """Проверяет значение на соответствие скомпилированному regex."""

    def __init__(self, regex: Optional[re.Pattern]) -> None:
        self.regex = regex

    def matches(self, value: object) -> bool:
        if self.regex is None:
            return False
        return self.regex.search(str(value)) is not None