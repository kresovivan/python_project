"""Комплексная проверка ВСЕХ функций программы.

Использует тестовые файлы examples/test_A.csv (разделитель «,») и
examples/test_B.csv (разделитель «;»), которые покрывают: дубли ключа,
отсутствующие записи, отличия значений, пробелы в ключе, лишние колонки.

Запуск:
    py -m unittest tests.test_all_functions -v

В песочнице/CI вывод можно перенаправить в доступную папку переменной окружения
TEST_TMPDIR (иначе используется tempfile).
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from table_compare import exporter as exporter_module
from table_compare.comparator import TableComparator
from table_compare.exporter import ReportExporter
from table_compare.loader import TableLoader
from table_compare.statistics import StatisticsAnalyzer

ROOT = Path(__file__).resolve().parents[1]
DATA_A = ROOT / 'examples' / 'test_A.csv'
DATA_B = ROOT / 'examples' / 'test_B.csv'


def writable_dir() -> Path:
    """Папка для выгружаемых файлов; настраивается через TEST_TMPDIR."""
    base = os.environ.get('TEST_TMPDIR')
    if base:
        d = Path(base) / 'tc_out'
        d.mkdir(parents=True, exist_ok=True)
        return d
    return Path(tempfile.mkdtemp(prefix='tc_'))


class LoaderTests(unittest.TestCase):
    """TableLoader: чтение CSV, Excel, листов, параллельная загрузка."""

    def setUp(self):
        self.loader = TableLoader()

    def test_read_any_file_autodetect_delimiters(self):
        a = self.loader.read_any_file(str(DATA_A))  # запятая
        b = self.loader.read_any_file(str(DATA_B))  # точка с запятой
        cols = ['Номер', 'Статус', 'Сумма', 'Дата', 'Комментарий']
        self.assertEqual(list(a.columns), cols)
        self.assertEqual(list(b.columns), cols)
        self.assertEqual(len(a), 9)
        self.assertEqual(len(b), 8)

    def test_read_csv_private(self):
        a = self.loader._read_csv(str(DATA_A))
        self.assertEqual(list(a.columns)[0], 'Номер')
        self.assertEqual(a['Номер'].iloc[0], '1')

    def test_load_files_parallel_with_progress(self):
        seen = []
        results = self.loader.load_files(
            [str(DATA_A), str(DATA_B)],
            progress_cb=lambda done, tot, path, elapsed, rows: seen.append(
                (done, tot, rows)))
        self.assertEqual(list(results.keys()), [str(DATA_A), str(DATA_B)])
        self.assertTrue(all(isinstance(df, pd.DataFrame) for df in results.values()))
        self.assertEqual([len(r) for r in results.values()], [9, 8])
        self.assertEqual([d for d, t, r in seen], [1, 2])

    def test_list_sheets_and_multisheet_read(self):
        out = writable_dir() / 'multi.xlsx'
        with pd.ExcelWriter(out, engine='openpyxl') as w:
            pd.DataFrame({'Номер': ['1'], 'Статус': ['Активен']}).to_excel(
                w, sheet_name='Лист 1', index=False)
            pd.DataFrame({'Номер': ['2'], 'Статус': ['Ожидание']}).to_excel(
                w, sheet_name='Лист 2', index=False)
        self.assertEqual(self.loader.list_sheets(str(out)), ['Лист 1', 'Лист 2'])
        both = self.loader.read_any_file(str(out), ['Лист 1', 'Лист 2'])
        self.assertEqual(len(both), 2)

    def test_read_any_file_rejects_diff_sheet_columns(self):
        out = writable_dir() / 'diff.xlsx'
        with pd.ExcelWriter(out, engine='openpyxl') as w:
            pd.DataFrame({'Номер': ['1']}).to_excel(w, sheet_name='Лист 1', index=False)
            pd.DataFrame({'Другое': ['2']}).to_excel(
                w, sheet_name='Лист 2', index=False)
        with self.assertRaises(ValueError):
            self.loader.read_any_file(str(out), ['Лист 1', 'Лист 2'])


class CompareTests(unittest.TestCase):
    """TableComparator: медленный и ускоренный пути, ключи, пропуски."""

    @classmethod
    def setUpClass(cls):
        cls.frames = {
            str(DATA_A): TableLoader().read_any_file(str(DATA_A)),
            str(DATA_B): TableLoader().read_any_file(str(DATA_B)),
        }

    def test_compare_duplicates_and_missing(self):
        result, stat = TableComparator(self.frames).compare(
            ['Номер'], ['Статус', 'Сумма'], ['Дата', 'Комментарий'])
        self.assertEqual(len(result), 10)
        self.assertEqual(stat, {'Совпадает': 5, 'Отличается': 3, 'Нет строки': 2})
        # пропуски — None, а не nan (ключ "3" отсутствует в test_B)
        self.assertIsNone(result['test_B::Комментарий'].iloc[2])

    def test_fast_path_unique_keys(self):
        frames = {
            'a.csv': pd.DataFrame({'Номер': ['1', '2'], 'Статус': ['Да', 'Да']}),
            'b.csv': pd.DataFrame({'Номер': ['1', '3'], 'Статус': ['Нет', 'Да']}),
        }
        result, stat = TableComparator(frames).compare(['Номер'], ['Статус'])
        self.assertEqual(stat, {'Совпадает': 0, 'Отличается': 1, 'Нет строки': 2})

    def test_whitespace_in_key_is_normalized(self):
        result, _ = TableComparator(self.frames).compare(['Номер'], ['Статус'])
        keys = result['Ключ'].tolist()
        self.assertIn('7', keys)       # " 7 " и "7" склеились в один ключ
        self.assertNotIn(' 7 ', keys)

    def test_missing_key_field_raises_clear_error(self):
        frames = {
            'a.csv': pd.DataFrame({'Другое поле': ['1']}),
            'b.csv': pd.DataFrame({'Другое поле': ['1']}),
        }
        with self.assertRaises(ValueError):
            TableComparator(frames).compare(['Номер'], ['Другое поле'])


class StatisticsTests(unittest.TestCase):
    def test_summarize(self):
        frames = {str(DATA_A): TableLoader().read_any_file(str(DATA_A)),
                  str(DATA_B): TableLoader().read_any_file(str(DATA_B))}
        result, _ = TableComparator(frames).compare(
            ['Номер'], ['Статус', 'Сумма'], ['Дата', 'Комментарий'])
        details = StatisticsAnalyzer(
            result, ['Статус', 'Сумма'], [str(DATA_A), str(DATA_B)]).summarize()
        self.assertEqual([f['missing'] for f in details['files']], [1, 1])
        by_field = {f['field']: f for f in details['fields']}
        self.assertEqual(by_field['Статус']['diff'], 3)
        self.assertEqual(by_field['Статус']['match'], 5)
        self.assertEqual(by_field['Сумма']['diff'], 2)


class ExporterTests(unittest.TestCase):
    """ReportExporter: CSV, HTML, XLSX (обычный и разбитый на листы)."""

    @classmethod
    def setUpClass(cls):
        cls.frames = {str(DATA_A): TableLoader().read_any_file(str(DATA_A)),
                      str(DATA_B): TableLoader().read_any_file(str(DATA_B))}
        cls.result, cls.stat = TableComparator(cls.frames).compare(
            ['Номер'], ['Статус', 'Сумма'], ['Дата', 'Комментарий'])
        cls.details = StatisticsAnalyzer(
            cls.result, ['Статус', 'Сумма'],
            [str(DATA_A), str(DATA_B)]).summarize()
        cls.metrics = {p: {'rows': len(df), 'seconds': 0.1}
                       for p, df in cls.frames.items()}

    def _exporter(self):
        return ReportExporter(self.result, self.stat, ['Номер'], self.details,
                              self.frames, self.metrics, 0.2, 0.1)

    def test_save_csv_and_html(self):
        d = writable_dir()
        self._exporter().save('csv', str(d / 'out.csv'))
        self._exporter().save('html', str(d / 'out.html'))
        df = pd.read_csv(str(d / 'out.csv'), sep=';')
        self.assertEqual(len(df), 10)
        self.assertIn('<table>', (d / 'out.html').read_text(encoding='utf-8-sig'))

    def test_to_html_static(self):
        html = ReportExporter.to_html(self.result.head(3))
        self.assertIn('<table>', html)
        self.assertIn('<meta charset="utf-8">', html)

    def test_save_xlsx_normal(self):
        import openpyxl
        d = writable_dir()
        self._exporter().save('xlsx', str(d / 'out.xlsx'))
        book = openpyxl.load_workbook(str(d / 'out.xlsx'))
        self.assertEqual(book.sheetnames, ['Сводка', 'Результаты'])
        self.assertEqual(book['Результаты'].max_row, 11)  # заголовок + 10 строк

    def test_save_xlsx_large_splits_sheets(self):
        import openpyxl
        d = writable_dir()
        xlsx = d / 'large.xlsx'
        with patch.object(exporter_module, 'EXCEL_MAX_DATA_ROWS', 4):
            self._exporter().save_xlsx(str(xlsx))
        book = openpyxl.load_workbook(str(xlsx))
        self.assertEqual(book.sheetnames,
                         ['Сводка', 'Результаты 1', 'Результаты 2', 'Результаты 3'])
        # 10 строк при лимите 4 -> листы по 4 + 4 + 2 строки данных
        self.assertEqual([book[n].max_row for n in book.sheetnames[1:]],
                         [5, 5, 3])
        # разбитую книгу можно снова прочитать программой
        loader = TableLoader()
        restored = loader.read_any_file(str(xlsx), book.sheetnames[1:])
        self.assertEqual(len(restored), 10)


if __name__ == '__main__':
    unittest.main()