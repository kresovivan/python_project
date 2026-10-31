"""Показатели по полям и по загруженным файлам."""

import os
from typing import List

import pandas as pd

from .config import STATUS_MATCH, STATUS_DIFF, STATUS_SUFFIX


class StatisticsAnalyzer:
    def __init__(self, result: pd.DataFrame, fields: List[str],
                 file_names: List[str]):
        self.result = result
        self.fields = fields
        self.file_names = file_names

    def summarize(self) -> dict:
        """Разделить итоги по записям и значениям полей.

        В статистику поля входят лишь записи, доступные для сравнения
        во всех файлах. Отсутствующие записи считаются отдельно.
        """
        result, fields, file_names = (
            self.result, self.fields, self.file_names)
        per_field = []
        for field in fields:
            column = field + STATUS_SUFFIX
            if column not in result:
                continue
            counts = result[column].value_counts()
            per_field.append({
                'field': field,
                'match': int(counts.get(STATUS_MATCH, 0)),
                'diff': int(counts.get(STATUS_DIFF, 0)),
                'checked': int(counts.get(STATUS_MATCH, 0) +
                               counts.get(STATUS_DIFF, 0)),
            })
        per_field.sort(key=lambda row: row['diff'], reverse=True)

        per_file = []
        for path in file_names:
            short = os.path.splitext(os.path.basename(path))[0]
            column = short + '::ключ'
            per_file.append({
                'file': os.path.basename(path),
                'missing': int(result[column].isna().sum())
                if column in result else 0,
            })
        return {'fields': per_field, 'files': per_file}
