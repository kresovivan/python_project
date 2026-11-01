# =============================================================================
# СЛОВАРЬ - загружает слова из папки data/ и отвечает на вопросы о них
# =============================================================================
#
# Формат файлов data/*.txt - одна строка = одно слово, поля через "|":
#
#     # topic: Название темы        (с этой строки начинается тема)
#     variable|переменная|вэриабл   (английский|русский|произношение)
#     print|печатать|принт|print("Hi") - вывод   (4-е поле: пример, необязательно)
#
# Строки, начинающиеся с "#", - комментарии. Пустые строки пропускаются.
# Если слово уже встречалось в другой теме - повтор пропускается.

import random
from pathlib import Path

from core.models import Word


class Vocabulary:
    """Все слова, разложенные по темам."""

    def __init__(self, data_dir: Path):
        # Словарь: ключ - название темы, значение - список слов этой темы.
        # Подчёркивание в начале имени (_topics) - договорённость в Python:
        # "это внутренняя деталь класса, снаружи напрямую не трогать".
        self._topics: dict[str, list[Word]] = {}
        # Быстрый поиск слова по английскому написанию - нужен, чтобы
        # восстановить незаконченное занятие по сохранённым ключам.
        self._by_en: dict[str, Word] = {}
        self._load(data_dir)

    # --- загрузка ------------------------------------------------------------

    def _load(self, data_dir: Path) -> None:
        seen = set()  # уже загруженные слова - чтобы не было повторов
        # sorted() - файлы читаются по порядку имён: 00_..., 01_..., 02_...
        for path in sorted(data_dir.glob("*.txt")):
            topic = path.stem  # имя файла без .txt - тема по умолчанию
            lines = path.read_text(encoding="utf-8").splitlines()
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
                    raise ValueError(f"{path.name}, строка {line_no}: нужно минимум 3 поля через |")

                en, ru, sound = parts[0], parts[1], parts[2]
                example = parts[3] if len(parts) > 3 else ""

                word = Word(en=en, ru=ru, sound=sound, topic=topic, example=example)
                # Повтор определяем по слову без пояснения в скобках:
                # "check" и "check (text)" - одно и то же слово.
                if word.answer.lower() in seen:
                    continue
                seen.add(word.answer.lower())
                self._topics.setdefault(topic, []).append(word)
                self._by_en[word.en] = word

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

    def search(self, text: str) -> list[Word]:
        """Найти слова, где текст встречается в английском слове или переводе."""
        text = text.lower()
        return [w for w in self.all_words() if text in w.en.lower() or text in w.ru.lower()]
