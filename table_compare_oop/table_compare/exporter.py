"""Выгрузка полного результата в CSV, XLSX и HTML."""

import os
import tempfile

import pandas as pd

from .config import (
    STATUS_SUFFIX, STATUS_MATCH, STATUS_DIFF, STATUS_MISSING,
    COLOR_MATCH, COLOR_DIFF, COLOR_MISSING,
)

EXCEL_MAX_DATA_ROWS = 1_048_575


class ReportExporter:
    def __init__(self, result_df, last_stat, last_key_fields,
                 detail_stats, frames, load_metrics,
                 load_elapsed, compare_elapsed, progress_cb=None):
        self.result_df = result_df
        self.last_stat = last_stat
        self.last_key_fields = last_key_fields
        self.detail_stats = detail_stats
        self.frames = frames
        self.load_metrics = load_metrics
        self.load_elapsed = load_elapsed
        self.compare_elapsed = compare_elapsed
        self.progress_cb = progress_cb

    def save(self, fmt, path):
        if fmt == 'xlsx':
            self.save_xlsx(path)
        elif fmt == 'csv':
            self.result_df.to_csv(path, index=False, sep=';',
                                  encoding='utf-8-sig')
        elif fmt == 'html':
            with open(path, 'w', encoding='utf-8-sig') as output:
                output.write(self.to_html(self.result_df))
        else:
            raise ValueError('Неизвестный формат: ' + fmt)

    def save_xlsx(self, path):
        """Выгрузить понятную сводку и полные результаты в один файл."""
        from openpyxl.formatting.rule import DataBarRule
        from openpyxl.styles import Alignment, Font, PatternFill
        from openpyxl.utils import get_column_letter

        if len(self.result_df) > EXCEL_MAX_DATA_ROWS:
            return self._save_large_xlsx(path)
        with pd.ExcelWriter(path, engine='openpyxl') as writer:
            self.result_df.to_excel(writer, sheet_name='Результаты',
                                    index=False)
            book = writer.book
            sheet = book.create_sheet('Сводка', 0)
            sheet.sheet_view.showGridLines = False
            sheet.merge_cells('A1:F1')
            sheet['A1'] = 'Результаты сравнения таблиц'
            sheet['A1'].font = Font(size=17, bold=True, color='17365D')
            sheet['A3'], sheet['B3'] = 'Ключ', ' + '.join(self.last_key_fields)
            sheet.merge_cells('A4:E4')
            sheet['A4'] = 'Итог по записям - каждая запись учтена один раз'
            sheet['A4'].font = Font(bold=True, color='17365D')
            for line, (label, value) in enumerate((
                    ('Всего записей', len(self.result_df)),
                    ('Совпало', self.last_stat.get(STATUS_MATCH, 0)),
                    ('Отличается', self.last_stat.get(STATUS_DIFF, 0)),
                    ('Без пары по ключу',
                     self.last_stat.get(STATUS_MISSING, 0)),
                    ('Загрузка, с', round(self.load_elapsed, 2)),
                    ('Сопоставление, с', round(self.compare_elapsed, 2))),
                    start=5):
                sheet.cell(line, 1, label)
                sheet.cell(line, 2, value)
            fields_title_row = 12
            fields_note_row = fields_title_row + 1
            fields_header_row = fields_title_row + 2
            sheet.merge_cells(start_row=fields_title_row, start_column=1,
                              end_row=fields_title_row, end_column=5)
            sheet.cell(fields_title_row, 1,
                       'По полям - только записи, имеющиеся во всех файлах'
                       ).font = Font(bold=True, color='17365D')
            sheet.merge_cells(start_row=fields_note_row, start_column=1,
                              end_row=fields_note_row, end_column=5)
            sheet.cell(fields_note_row, 1,
                       'Одна запись может отличаться сразу в нескольких полях.'
                       ).font = Font(italic=True, color='637487')
            headers = ('Поле', 'Проверено', 'Совпало', 'Отличается',
                       'Совпало, %')
            for col, value in enumerate(headers, 1):
                sheet.cell(fields_header_row, col, value)
            for row_number, item in enumerate(
                    self.detail_stats['fields'], fields_header_row + 1):
                total = item['checked']
                for column, value in enumerate((
                        item['field'], total, item['match'], item['diff'],
                        round(100 * item['match'] / total, 1)
                        if total else None), 1):
                    sheet.cell(row_number, column, value)
            for col in range(1, 6):
                head = sheet.cell(fields_header_row, col)
                head.fill = PatternFill('solid', fgColor='234A72')
                head.font = Font(color='FFFFFF', bold=True)
                head.alignment = Alignment(horizontal='center')

            count = len(self.detail_stats['fields'])
            sheet.merge_cells('G3:I3')
            sheet['G3'] = 'Поля с отличиями значений'
            sheet['G3'].font = Font(size=14, bold=True, color='17365D')
            sheet['G5'] = 'Поле'
            sheet['H5'] = 'Записей'
            sheet['I5'] = 'Сравнение по количеству'
            for column in ('G', 'H', 'I'):
                cell = sheet[f'{column}5']
                cell.fill = PatternFill('solid', fgColor='234A72')
                cell.font = Font(color='FFFFFF', bold=True)

            # Название и точное число стоят рядом с полосой Excel.
            chart_fields = sorted(self.detail_stats['fields'],
                                  key=lambda item: item['diff'],
                                  reverse=True)[:12]
            maximum = max((item['diff'] for item in chart_fields), default=0)
            for index, item in enumerate(chart_fields, start=6):
                sheet.cell(index, 7, item['field'])
                sheet.cell(index, 8, item['diff'])
                bar = sheet.cell(index, 9, item['diff'])
                bar.number_format = ';;;'
                sheet.row_dimensions[index].height = 23
            if chart_fields:
                sheet.conditional_formatting.add(
                    'I6:I{}'.format(5 + len(chart_fields)),
                    DataBarRule(start_type='num', start_value=0,
                                end_type='num', end_value=max(maximum, 1),
                                color='4472C4', showValue=False))
            note_row = 7 + len(chart_fields)
            if count > len(chart_fields):
                sheet.cell(note_row, 7,
                           'Показаны 12 полей с наибольшим числом отличий.')
                note_row += 1
            sheet.column_dimensions['G'].width = 36
            sheet.column_dimensions['H'].width = 16
            sheet.column_dimensions['I'].width = 28

            start = fields_header_row + count + 3
            sheet.merge_cells(start_row=start - 1, start_column=1,
                              end_row=start - 1, end_column=4)
            sheet.cell(start - 1, 1,
                       'Загрузка файлов'
                       ).font = Font(bold=True, color='17365D')
            sheet.cell(start, 1, 'Файл')
            sheet.cell(start, 2, 'Строк')
            sheet.cell(start, 3, 'Загрузка, с')
            sheet.cell(start, 4, 'Строк/с')
            for col in range(1, 5):
                head = sheet.cell(start, col)
                head.fill = PatternFill('solid', fgColor='234A72')
                head.font = Font(color='FFFFFF', bold=True)
            for index, item in enumerate(self.detail_stats['files'], start + 1):
                file_path = next((p for p in self.frames
                                  if os.path.basename(p) == item['file']), None)
                metric = self.load_metrics.get(file_path, {})
                seconds = metric.get('seconds', 0)
                for col, value in enumerate((
                        item['file'], metric.get('rows', 0), round(seconds, 2),
                        round(metric.get('rows', 0) / seconds)
                        if seconds else 0), 1):
                    sheet.cell(index, col, value)

            for col, width in {'A': 40, 'B': 20, 'C': 22,
                               'D': 20, 'E': 20}.items():
                sheet.column_dimensions[col].width = width
            data_sheet = book['Результаты']
            data_sheet.freeze_panes = 'C2'
            data_sheet.auto_filter.ref = data_sheet.dimensions
            for index, value in enumerate(self.result_df.columns, 1):
                data_sheet.column_dimensions[
                    get_column_letter(index)].width = min(40, max(16, len(value) + 3))
                cell = data_sheet.cell(1, index)
                cell.fill = PatternFill('solid', fgColor='234A72')
                cell.font = Font(color='FFFFFF', bold=True)


    def _save_large_xlsx(self, path):
        """Записать большую книгу последовательно, не храня листы в памяти."""
        from openpyxl import Workbook
        from openpyxl.cell import WriteOnlyCell
        from openpyxl.formatting.rule import DataBarRule
        from openpyxl.styles import Font, PatternFill
        from openpyxl.utils import get_column_letter

        if len(self.result_df.columns) > 16_384:
            raise ValueError('Excel поддерживает не более 16 384 столбцов.')

        book = Workbook(write_only=True)
        summary = book.create_sheet('Сводка')
        summary.sheet_view.showGridLines = False
        summary.column_dimensions['A'].width = 40
        for col, width in {'B': 20, 'C': 22, 'D': 20, 'E': 20,
                           'G': 36, 'H': 16, 'I': 28}.items():
            summary.column_dimensions[col].width = width

        cells = {}

        def put(row, col, value, style=None):
            cells[(row, col)] = value, style

        put(1, 1, 'Результаты сравнения таблиц', 'title')
        put(3, 1, 'Ключ')
        put(3, 2, ' + '.join(self.last_key_fields))
        put(4, 1, 'Итог по записям - каждая запись учтена один раз', 'section')
        for row, (label, value) in enumerate((
                ('Всего записей', len(self.result_df)),
                ('Совпало', self.last_stat.get(STATUS_MATCH, 0)),
                ('Отличается', self.last_stat.get(STATUS_DIFF, 0)),
                ('Без пары по ключу', self.last_stat.get(STATUS_MISSING, 0)),
                ('Загрузка, с', round(self.load_elapsed, 2)),
                ('Сопоставление, с', round(self.compare_elapsed, 2))), 5):
            put(row, 1, label)
            put(row, 2, value)

        put(12, 1, 'По полям - только записи, имеющиеся во всех файлах',
            'section')
        put(13, 1, 'Одна запись может отличаться сразу в нескольких полях.',
            'note')
        for col, title in enumerate(('Поле', 'Проверено', 'Совпало',
                                     'Отличается', 'Совпало, %'), 1):
            put(14, col, title, 'header')
        for row, item in enumerate(self.detail_stats['fields'], 15):
            checked = item['checked']
            for col, value in enumerate((
                    item['field'], checked, item['match'], item['diff'],
                    round(100 * item['match'] / checked, 1)
                    if checked else None), 1):
                put(row, col, value)

        chart_fields = sorted(self.detail_stats['fields'],
                              key=lambda item: item['diff'],
                              reverse=True)[:12]
        put(3, 7, 'Поля с отличиями значений', 'section')
        for col, title in enumerate(('Поле', 'Записей',
                                     'Сравнение по количеству'), 7):
            put(5, col, title, 'header')
        for row, item in enumerate(chart_fields, 6):
            put(row, 7, item['field'])
            put(row, 8, item['diff'])
            put(row, 9, item['diff'], 'bar')
        if chart_fields:
            summary.conditional_formatting.add(
                'I6:I{}'.format(5 + len(chart_fields)),
                DataBarRule(start_type='num', start_value=0,
                            end_type='num',
                            end_value=max(1, max(item['diff']
                                                 for item in chart_fields)),
                            color='4472C4', showValue=False))
        if len(self.detail_stats['fields']) > len(chart_fields):
            put(7 + len(chart_fields), 7,
                'Показаны 12 полей с наибольшим числом отличий.')

        start = 17 + len(self.detail_stats['fields'])
        put(start - 1, 1, 'Загрузка файлов', 'section')
        for col, title in enumerate(('Файл', 'Строк', 'Загрузка, с',
                                     'Строк/с'), 1):
            put(start, col, title, 'header')
        for row, item in enumerate(self.detail_stats['files'], start + 1):
            file_path = next((p for p in self.frames
                              if os.path.basename(p) == item['file']), None)
            metric = self.load_metrics.get(file_path, {})
            seconds = metric.get('seconds', 0)
            for col, value in enumerate((
                    item['file'], metric.get('rows', 0), round(seconds, 2),
                    round(metric.get('rows', 0) / seconds)
                    if seconds else 0), 1):
                put(row, col, value)

        header_fill = PatternFill('solid', fgColor='234A72')
        for row in range(1, max((position[0] for position in cells),
                                default=0) + 1):
            values = []
            for col in range(1, 10):
                value, style = cells.get((row, col), (None, None))
                cell = WriteOnlyCell(summary, value=value)
                if style == 'title':
                    cell.font = Font(size=17, bold=True, color='17365D')
                elif style == 'section':
                    cell.font = Font(bold=True, color='17365D')
                elif style == 'note':
                    cell.font = Font(italic=True, color='637487')
                elif style == 'header':
                    cell.fill = header_fill
                    cell.font = Font(color='FFFFFF', bold=True)
                elif style == 'bar':
                    cell.number_format = ';;;'
                values.append(cell)
            summary.append(values)

        columns = list(self.result_df.columns)
        last_column = get_column_letter(len(columns))
        written = 0
        for offset in range(0, max(len(self.result_df), 1),
                            EXCEL_MAX_DATA_ROWS):
            end = min(offset + EXCEL_MAX_DATA_ROWS, len(self.result_df))
            number = offset // EXCEL_MAX_DATA_ROWS + 1
            data = book.create_sheet('Результаты {}'.format(number))
            data.freeze_panes = 'C2'
            data.auto_filter.ref = 'A1:{}{}'.format(last_column,
                                                    end - offset + 1)
            header = []
            for index, name in enumerate(columns, 1):
                data.column_dimensions[get_column_letter(index)].width = min(
                    40, max(16, len(str(name)) + 3))
                cell = WriteOnlyCell(data, value=name)
                cell.fill = header_fill
                cell.font = Font(color='FFFFFF', bold=True)
                header.append(cell)
            data.append(header)
            for values in self.result_df.iloc[offset:end].itertuples(
                    index=False, name=None):
                row = []
                for value in values:
                    if value is None:
                        row.append(None)
                    elif isinstance(value, str):
                        if value.startswith('='):
                            cell = WriteOnlyCell(data, value=value)
                            cell.data_type = 's'
                            row.append(cell)
                        else:
                            row.append(value)
                    elif pd.isna(value):
                        row.append(None)
                    else:
                        row.append(value)
                data.append(row)
                written += 1
                if self.progress_cb and written % 25_000 == 0:
                    self.progress_cb(written, len(self.result_df))

        output_dir = os.path.dirname(os.path.abspath(path))
        handle, temp_path = tempfile.mkstemp(dir=output_dir, suffix='.xlsx')
        os.close(handle)
        try:
            book.save(temp_path)
            os.replace(temp_path, path)
            if self.progress_cb:
                self.progress_cb(len(self.result_df), len(self.result_df))
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    @staticmethod
    def to_html(df):
        status_cols = [c for c in df.columns if c.endswith(STATUS_SUFFIX)]
        color = {STATUS_MATCH: COLOR_MATCH,
                 STATUS_DIFF: COLOR_DIFF,
                 STATUS_MISSING: COLOR_MISSING}

        css = (
            '<style>'
            'table{border-collapse:collapse;font-family:sans-serif;font-size:13px}'
            'th,td{border:1px solid #bbb;padding:6px 10px;text-align:left;'
            'vertical-align:top}'
            'th{background:#f0f0f0}'
            '</style>'
        )

        head = ''.join('<th>' + str(c) + '</th>' for c in df.columns)
        body_parts = []
        for _, r in df.iterrows():
            statuses = [str(r[c]).strip() for c in status_cols
                        if not pd.isna(r[c])]
            if STATUS_MISSING in statuses:
                bg = color[STATUS_MISSING]
            elif STATUS_DIFF in statuses:
                bg = color[STATUS_DIFF]
            else:
                bg = color[STATUS_MATCH]
            cells = ''.join(
                '<td>' + ('' if pd.isna(r[c]) else str(r[c])) + '</td>'
                for c in df.columns)
            body_parts.append(
                '<tr style="background:' + bg + '">' + cells + '</tr>')

        return (
            '<!DOCTYPE html><html><head>'
            '<meta charset="utf-8">'
            '<meta http-equiv="Content-Type" '
            'content="text/html; charset=utf-8">'
            + css +
            '</head><body><table><thead><tr>' + head +
            '</tr></thead><tbody>' + ''.join(body_parts) +
            '</tbody></table></body></html>'
        )
