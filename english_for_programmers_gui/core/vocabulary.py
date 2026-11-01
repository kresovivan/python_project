# =============================================================================
# СЛОВАРЬ - все слова программы, разложенные по темам
# =============================================================================
#
# Что это в жизни: "бумажный словарь с закладками по темам". Его можно
# открыть на теме, найти слово, взять случайные слова для упражнения.
# Сам словарь ничего не знает о прогрессе ученика: это просто книга.
#
# Формат файлов data/*.txt - одна строка = одно слово, поля через "|":
#
#     # topic: Название темы        (с этой строки начинается тема)
#     variable|переменная|вэриабл   (английский|русский|произношение)
#     print|печатать|принт|print("Hi") - вывод   (4-е поле: пример, необязательно)
#
# Строки, начинающиеся с "#", - комментарии. Пустые строки пропускаются.
# Если слово уже встречалось в другой теме - повтор пропускается.
#
# Устройство файла:
#   parse_words()           - разбирает ТЕКСТ в слова (без файлов: легко проверить);
#   Vocabulary              - словарь из готовых слов;
#   Vocabulary.from_folder  - прочитать все файлы папки data/ (так делает программа);
#   Vocabulary.from_text    - собрать словарь из строки (так удобно в тестах).
#
# Кто пользуется: Lesson берёт слова для занятия, ChoiceQuestion - неправильные
# варианты, страница "Словарь" - поиск.

import random
from collections.abc import Iterable, Iterator
from pathlib import Path

from core.models import Word


def parse_words(lines: Iterable[str], source: str, topic: str) -> Iterator[Word]:
    """Разобрать строки формата data/*.txt в слова.

    source - откуда строки (имя файла): нужно для понятного сообщения об ошибке.
    topic - тема по умолчанию, пока в тексте не встретилась строка "# topic:".

    yield вместо return превращает функцию в генератор: слова отдаются по одному,
    по мере чтения, а не собираются сначала в большой список.
    """
    for line_no, line in enumerate(lines, start=1):
        line = line.strip()
        if not line:
            continue
        if line.startswith("#"):
            if line.lower().startswith("# topic:"):
                topic = line.split(":", 1)[1].strip()
            continue

        parts = [part.strip() for part in line.split("|")]
        if len(parts) < 3:
            raise ValueError(f"{source}, строка {line_no}: нужно минимум 3 поля через |")
        en, ru, sound = parts[0], parts[1], parts[2]
        example = parts[3] if len(parts) > 3 else ""
        yield Word(en=en, ru=ru, sound=sound, topic=topic, example=example)


class Vocabulary:
    """Все слова, разложенные по темам."""

    # --- создание ------------------------------------------------------------

    def __init__(self, words: Iterable[Word]):
        # Словарь: ключ - название темы, значение - список слов этой темы.
        # Подчёркивание в начале имени (_topics) - договорённость в Python:
        # "это внутренняя деталь класса, снаружи напрямую не трогать".
        self._topics: dict[str, list[Word]] = {}
        # Быстрый поиск слова по английскому написанию - нужен, чтобы
        # восстановить незаконченное занятие по сохранённым ключам.
        self._by_en: dict[str, Word] = {}
        seen = set()  # уже добавленные слова - чтобы не было повторов
        for word in words:
            # Повтор определяем по слову без пояснения в скобках:
            # "check" и "check (text)" - одно и то же слово.
            if word.answer.lower() in seen:
                continue
            seen.add(word.answer.lower())
            self._topics.setdefault(word.topic, []).append(word)
            self._by_en[word.en] = word

    @classmethod
    def from_folder(cls, folder: Path) -> "Vocabulary":
        """Прочитать все файлы *.txt папки. Тема по умолчанию - имя файла.

        sorted() - файлы читаются по порядку имён: 00_..., 01_..., 02_...
        """
        words: list[Word] = []
        for path in sorted(folder.glob("*.txt")):
            lines = path.read_text(encoding="utf-8").splitlines()
            words.extend(parse_words(lines, source=path.name, topic=path.stem))
        return cls(words)

    @classmethod
    def from_text(cls, text: str, topic: str = "Слова") -> "Vocabulary":
        """Собрать словарь из текста в формате data/*.txt."""
        return cls(parse_words(text.splitlines(), source="текст", topic=topic))

    # --- вопросы к словарю ---------------------------------------------------

    def topics(self) -> list[str]:
        """Названия всех тем."""
        return list(self._topics.keys())

    def get(self, en: str) -> Word | None:
        """Слово по английскому написанию (или None, если его нет)."""
        return self._by_en.get(en)

    def words(self, topic: str) -> list[Word]:
        """Слова одной темы (копия списка - чтобы снаружи не испортили)."""
        return self._topics[topic].copy()

    def all_words(self) -> list[Word]:
        """Все слова одним списком."""
        result = []
        for words in self._topics.values():
            result.extend(words)
        return result

    def __len__(self) -> int:
        # Специальный (магический) метод: позволяет писать len(vocabulary).
        return sum(len(words) for words in self._topics.values())

    def search(self, text: str) -> list[Word]:
        """Слова, где текст встречается в английском слове или переводе.

        Порядок - от самого похожего на запрос:
          1. точное совпадение ("loop" для запроса "loop");
          2. слова, которые начинаются с запроса ("loopback");
          3. остальные, где запрос внутри ("for loop"); короткие - раньше.
        """
        query = text.lower()
        found = [w for w in self.all_words() if query in w.en.lower() or query in w.ru.lower()]
        # Ключ сортировки - кортеж. Кортежи сравниваются по порядку элементов,
        # а False < True, поэтому "совпало" (False в "не совпало") идёт раньше.
        found.sort(
            key=lambda w: (
                w.answer.lower() != query,
                not w.en.lower().startswith(query),
                len(w.en),
            )
        )
        return found

    # --- варианты для "Выбора перевода" ------------------------------------------

    def distractors(self, word: Word, count: int = 3) -> list[str]:
        """Неправильные варианты перевода для теста с выбором ответа.

        Берём их из той же темы - так тест сложнее и полезнее.
        Если в теме слов мало - добираем из всего словаря.
        """
        candidates = self._unique_translations(self._topics[word.topic], word)
        if len(candidates) < count:
            candidates = self._unique_translations(self.all_words(), word)
        return random.sample(candidates, count)

    @staticmethod
    def _unique_translations(words: list[Word], word: Word) -> list[str]:
        """Разные переводы слов из списка, кроме перевода самого слова.

        В словаре есть синонимы с одинаковым переводом: "shut down" и
        "turn off" - оба "выключить". Если брать переводы как есть, среди
        вариантов ответа могли оказаться два одинаковых "выключить".

        dict.fromkeys(...) убирает повторы и, в отличие от set(), сохраняет
        порядок. Порядок важен: при одном и том же random.seed() варианты
        будут одни и те же - так программу проще проверять тестами.
        """
        translations = dict.fromkeys(w.ru for w in words if w.ru != word.ru)
        return list(translations)
