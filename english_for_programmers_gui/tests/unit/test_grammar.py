# Тетради с правилами в таблицах:
#   core/grammar.py     - грамматика английского;
#   core/grammar_zh.py  - грамматика китайского;
#   core/pinyin.py      - китайские "Звуки и тоны".
# Все три устроены одинаково (темы, разделы, таблицы), поэтому проверяются
# одними и теми же тестами.
#
# Проверяется не содержание (его читают глазами), а то, что таблицы
# правильно заполнены: страница не должна сломаться на кривой строке.

import unittest

from core import grammar, grammar_zh, pinyin

BOOKS = {
    "грамматика английского": grammar.TOPICS,
    "грамматика китайского": grammar_zh.TOPICS,
    "звуки и тоны": pinyin.TOPICS,
}


def all_tables():
    """Все таблицы всех тем всех тетрадей: (название темы, таблица)."""
    return [
        (topic.title, table)
        for topics in BOOKS.values()
        for topic in topics
        for table in topic.tables
    ]


class TopicsTests(unittest.TestCase):
    """Каждую тетрадь проверяем отдельно: subTest показывает, в какой ошибка."""

    def test_there_are_topics(self):
        for book, topics in BOOKS.items():
            with self.subTest(book=book):
                self.assertTrue(topics)

    def test_topic_titles_are_unique(self):
        for book, topics in BOOKS.items():
            with self.subTest(book=book):
                titles = [topic.title for topic in topics]

                self.assertEqual(len(titles), len(set(titles)))

    def test_every_topic_has_explanation_and_table(self):
        for book, topics in BOOKS.items():
            with self.subTest(book=book):
                empty = [t.title for t in topics if not (t.intro and t.tables)]

                self.assertEqual(empty, [])

    def test_every_topic_has_section(self):
        """Раздел нужен оглавлению: темы сгруппированы под подписями "Основы", "Времена"..."""
        for book, topics in BOOKS.items():
            with self.subTest(book=book):
                without = [topic.title for topic in topics if not topic.section]

                self.assertEqual(without, [])

    def test_topics_of_one_section_go_together(self):
        """Раздел не разорван: иначе в оглавлении одна подпись появилась бы дважды."""
        for book, topics in BOOKS.items():
            with self.subTest(book=book):
                sections = [topic.section for topic in topics]
                blocks = [
                    s for i, s in enumerate(sections) if i == 0 or s != sections[i - 1]
                ]

                self.assertEqual(len(blocks), len(set(blocks)))


class TablesTests(unittest.TestCase):
    def test_every_row_has_as_many_cells_as_header(self):
        wrong = [
            (title, row)
            for title, table in all_tables()
            for row in table.rows
            if len(row) != len(table.headers)
        ]

        self.assertEqual(wrong, [])

    def test_no_empty_cells(self):
        """Пустая клетка выглядит как ошибка. Если писать нечего - ставим "-"."""
        empty = [
            (title, row)
            for title, table in all_tables()
            for row in table.rows
            if not all(cell.strip() for cell in row)
        ]

        self.assertEqual(empty, [])

    def test_spoken_columns_exist(self):
        """Колонки с текстом для озвучки (по щелчку) есть в таблице."""
        wrong = [
            (title, table.headers)
            for title, table in all_tables()
            if any(column >= len(table.headers) for column in table.speak_columns)
        ]

        self.assertEqual(wrong, [])


if __name__ == "__main__":
    unittest.main()
