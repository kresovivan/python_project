"""Объединение CSV-файлов без UI.

Отдельный модуль, чтобы логику можно было использовать в скриптах
и тестировать без Tkinter.
"""

import csv
import os
from typing import List, Tuple


def merge_csv_files(
    paths: List[str],
    out_path: str,
    delimiter: str = ';',
) -> Tuple[int, int, List[str]]:
    """Объединяет CSV-файлы в один.

    Колонки берутся из первого непустого файла, порядок колонок
    сохраняется. Пустые файлы пропускаются.
    Возвращает (файлов, строк данных, колонки).
    """
    prepared: List[Tuple[str, List[str], List[List[str]]]] = []
    columns: List[str] = []

    for path in paths:
        header, rows = _read_file(path, delimiter)
        if not header and not rows:
            continue
        if not rows:
            continue
        if not columns:
            columns = list(header)
        prepared.append((path, header, rows))

    if not prepared or not columns:
        raise RuntimeError('Все выбранные файлы пусты.')

    # Индекс колонки в результирующем файле.
    idx = {c: i for i, c in enumerate(columns)}

    total_rows = 0
    files_count = 0

    with open(out_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f, delimiter=delimiter)
        writer.writerow(columns)

        for _path, header, rows in prepared:
            src = {i: name for i, name in enumerate(header)}

            for row in rows:
                if not row:
                    continue
                if all((x or '').strip() == '' for x in row):
                    continue
                out = [''] * len(columns)
                for i, val in enumerate(row):
                    name = src.get(i)
                    if name is None:
                        continue
                    j = idx.get(name)
                    if j is None:
                        continue
                    out[j] = val
                writer.writerow(out)
                total_rows += 1
            files_count += 1

    return files_count, total_rows, columns


def _read_file(path: str,
               delimiter: str = ';') -> Tuple[List[str], List[List[str]]]:
    """Читает CSV-файл, возвращает (заголовки, строки)."""
    with open(path, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.reader(f, delimiter=delimiter)
        try:
            header = next(reader)
        except StopIteration:
            return [], []
        rows = [r for r in reader]
    return header, rows


def list_csv_files(folder: str) -> List[str]:
    """Возвращает отсортированный список CSV-файлов в папке."""
    if not os.path.isdir(folder):
        return []
    return sorted(
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.lower().endswith('.csv')
        and os.path.isfile(os.path.join(folder, f))
    )