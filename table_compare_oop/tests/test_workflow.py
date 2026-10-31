"""Проверка сохранения результатов после разделения программы на модули."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import openpyxl
import pandas as pd

from table_compare.comparator import TableComparator
from table_compare import exporter as exporter_module
from table_compare.exporter import ReportExporter
from table_compare.loader import TableLoader
from table_compare.statistics import StatisticsAnalyzer


ROOT = Path(__file__).resolve().parents[1]
FIELDS = ['Статус', 'Сумма', 'Дата', 'Ответственный']


class WorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        paths = [str(ROOT / 'examples' / f'compare_{label}_500.csv')
                 for label in ('A', 'B')]
        cls.frames = {path: TableLoader().read_any_file(path)
                      for path in paths}
        cls.result, cls.stat = TableComparator(cls.frames).compare(
            ['Номер'], FIELDS)
        cls.details = StatisticsAnalyzer(
            cls.result, FIELDS, paths).summarize()

    def test_comparison_and_missing_keys(self):
        self.assertEqual([len(f) for f in self.frames.values()], [500, 500])
        self.assertEqual(len(self.result), 510)
        self.assertEqual(self.stat, {
            'Совпадает': 478, 'Отличается': 12, 'Нет строки': 20})
        self.assertEqual([row['missing'] for row in self.details['files']],
                         [10, 10])
        self.assertEqual(
            self.details['fields'][0]['checked'], 490)

    def test_duplicate_keys_keep_their_occurrences(self):
        frames = {
            'first.csv': pd.DataFrame({
                'Номер': ['K', 'K'], 'Статус': ['Да', 'Нет']}),
            'second.csv': pd.DataFrame({
                'Номер': ['K', 'K'], 'Статус': ['Да', 'Ожидание']}),
        }
        result, stat = TableComparator(frames).compare(
            ['Номер'], ['Статус'])
        self.assertEqual(len(result), 2)
        self.assertEqual(stat, {
            'Совпадает': 1, 'Отличается': 1, 'Нет строки': 0})

    def test_unique_key_comparison_with_unmatched_rows(self):
        frames = {
            'first.csv': pd.DataFrame({
                'Номер': [' 1 ', '2', '4'],
                'Статус': ['Да', 'Да', 'Да'],
                'Комментарий': ['A', 'B', 'C']}),
            'second.csv': pd.DataFrame({
                'Номер': ['1', '3', '4'],
                'Статус': ['Да', 'Нет', 'Нет']}),
        }
        result, stat = TableComparator(frames).compare(
            ['Номер'], ['Статус', 'Номер'], ['Комментарий'])
        self.assertEqual(result['Ключ'].tolist(), ['1', '2', '3', '4'])
        self.assertEqual(stat, {
            'Совпадает': 1, 'Отличается': 1, 'Нет строки': 2})
        self.assertEqual(result['first::Номер'].iloc[0], '1')
        self.assertEqual(result['Статус::статус_сверки'].iloc[3], 'Отличается')
        self.assertEqual(result['second::Комментарий'].iloc[0], '')
        self.assertIsNone(result['second::Комментарий'].iloc[1])

    def test_unique_composite_key_with_missing_and_changed_rows(self):
        frames = {
            'first.csv': pd.DataFrame({
                'Код': ['1', '1', '2'], 'Дата': ['a', 'b', 'a'],
                'Статус': ['Да', 'Нет', 'Да']}),
            'second.csv': pd.DataFrame({
                'Код': ['1', '1', '2'], 'Дата': ['a', 'c', 'a'],
                'Статус': ['Да', 'Нет', 'Нет']}),
        }
        result, stat = TableComparator(frames).compare(
            ['Код', 'Дата'], ['Статус', 'Код'])
        self.assertEqual(result['Ключ'].tolist(),
                         ['1 | a', '1 | b', '1 | c', '2 | a'])
        self.assertEqual(stat, {
            'Совпадает': 1, 'Отличается': 1, 'Нет строки': 2})

    def test_duplicate_composite_key_keeps_occurrences(self):
        frames = {
            'first.csv': pd.DataFrame({
                'Код': ['1', '1'], 'Дата': ['a', 'a'],
                'Статус': ['Да', 'Нет']}),
            'second.csv': pd.DataFrame({
                'Код': ['1', '1'], 'Дата': ['a', 'a'],
                'Статус': ['Да', 'Ожидание']}),
        }
        result, stat = TableComparator(frames).compare(
            ['Код', 'Дата'], ['Статус'])
        self.assertEqual(len(result), 2)
        self.assertEqual(stat, {
            'Совпадает': 1, 'Отличается': 1, 'Нет строки': 0})

    def test_export_formats(self):
        metrics = {path: {'rows': 500, 'seconds': 0.1}
                   for path in self.frames}
        exporter = ReportExporter(
            self.result, self.stat, ['Номер'], self.details,
            self.frames, metrics, 0.2, 0.1)
        with tempfile.TemporaryDirectory() as directory:
            paths = {fmt: Path(directory) / ('report.' + fmt)
                     for fmt in ('xlsx', 'csv', 'html')}
            for fmt, path in paths.items():
                exporter.save(fmt, str(path))
            book = openpyxl.load_workbook(paths['xlsx'])
            self.assertEqual(book.sheetnames, ['Сводка', 'Результаты'])
            self.assertEqual(book['Сводка']['B8'].value, 20)
            self.assertEqual(book['Сводка']['I6'].data_type, 'n')
            self.assertEqual(book['Сводка']['I6'].value,
                             max(row['diff'] for row in self.details['fields']))
            self.assertEqual(len(book['Сводка'].conditional_formatting), 1)
            summary_text = [cell.value for row in book['Сводка']
                            for cell in row if isinstance(cell.value, str)]
            self.assertNotIn('Отсутствует записей', summary_text)
            self.assertFalse(any(value.startswith('Нет в ')
                                 for value in summary_text))
            self.assertIn('Загрузка файлов', summary_text)
            self.assertEqual(book['Результаты'].max_row, 511)
            self.assertEqual(
                len(pd.read_csv(paths['csv'], sep=';')), 510)
            self.assertIn(
                '<table>',
                paths['html'].read_text(encoding='utf-8-sig'))

    def test_large_excel_is_split_and_all_sheets_can_be_imported(self):
        excerpt = self.result.head(7).copy()
        excerpt.loc[excerpt.index[0], 'Ключ'] = '=текст'
        metrics = {path: {'rows': 500, 'seconds': 0.1}
                   for path in self.frames}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'split.xlsx'
            report = ReportExporter(
                excerpt, self.stat, ['Номер'], self.details,
                self.frames, metrics, 0.2, 0.1)
            with patch.object(exporter_module, 'EXCEL_MAX_DATA_ROWS', 3):
                report.save_xlsx(str(output))
            book = openpyxl.load_workbook(output)
            self.assertEqual(book.sheetnames,
                             ['Сводка', 'Результаты 1', 'Результаты 2',
                              'Результаты 3'])
            self.assertEqual([book[name].max_row for name in book.sheetnames[1:]],
                             [4, 4, 2])
            self.assertEqual(book['Сводка']['B5'].value, 7)
            self.assertEqual(book['Результаты 1']['A2'].data_type, 's')
            loader = TableLoader()
            self.assertEqual(loader.list_sheets(str(output)), book.sheetnames)
            restored = loader.read_any_file(str(output), book.sheetnames[1:])
            self.assertEqual(len(restored), 7)
            self.assertEqual(restored['Ключ'].tolist(),
                             excerpt['Ключ'].tolist())

    def test_import_rejects_different_sheet_columns(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'different.xlsx'
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                pd.DataFrame({'Номер': ['1']}).to_excel(
                    writer, sheet_name='Лист 1', index=False)
                pd.DataFrame({'Другой столбец': ['2']}).to_excel(
                    writer, sheet_name='Лист 2', index=False)
            with self.assertRaisesRegex(ValueError, 'отличаются названия'):
                TableLoader().read_any_file(str(output), ['Лист 1', 'Лист 2'])


if __name__ == '__main__':
    unittest.main()
