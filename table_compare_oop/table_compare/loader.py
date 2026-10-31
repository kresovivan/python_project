"""Загрузка CSV и Excel с учётом объёма файлов."""

import csv
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional

import pandas as pd

try:
    import chardet
except ImportError:
    chardet = None


class TableLoader:
    def __init__(self, max_workers=4, large_file_threshold=500 * 1024 * 1024):
        self.max_workers = max_workers
        self.large_file_threshold = large_file_threshold

    def _read_csv(self, path: str) -> pd.DataFrame:
        """Определить кодировку и разделитель, затем прочитать CSV."""
        with open(path, 'rb') as f:
            raw = f.read(200_000)
        enc = (chardet.detect(raw).get('encoding') if chardet else None) or 'utf-8-sig'

        sample = raw.decode(enc, errors='replace')
        sep = None
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=';,	|,')
            sep = dialect.delimiter
        except Exception:
            # Для типичных русскоязычных выгрузок чаще всего используется ';'.
            for candidate in (';', '	', '|', ','):
                if candidate in sample:
                    sep = candidate
                    break

        if sep is not None:
            try:
                return pd.read_csv(path, dtype=str, sep=sep,
                                   encoding=enc, engine='c')
            except Exception:
                pass

        # Резервный путь для нестандартного CSV.
        return pd.read_csv(path, dtype=str, sep=None,
                           engine='python', encoding=enc)


    @staticmethod
    def list_sheets(path: str) -> List[str]:
        """Вернуть названия листов Excel до загрузки данных."""
        with pd.ExcelFile(path) as workbook:
            return list(workbook.sheet_names)

    def read_any_file(self, path: str,
                      sheets: Optional[List[str]] = None) -> pd.DataFrame:
        """Прочитать Excel или CSV, сохранив значения столбцов как строки."""
        ext = os.path.splitext(path)[1].lower()
        if ext in ('.xlsx', '.xls', '.xlsm'):
            with pd.ExcelFile(path) as workbook:
                names = sheets if sheets is not None else workbook.sheet_names[:1]
                if not names:
                    raise ValueError('Не выбраны листы Excel: ' + os.path.basename(path))
                missing = [name for name in names
                           if name not in workbook.sheet_names]
                if missing:
                    raise ValueError('Лист не найден: ' + ', '.join(missing))
                tables = [workbook.parse(sheet_name=name, dtype=str)
                          for name in names]
            first = list(tables[0].columns)
            for name, table in zip(names[1:], tables[1:]):
                if set(table.columns) != set(first):
                    raise ValueError(
                        'На листе "{}" отличаются названия столбцов. '
                        'Выберите листы с одинаковыми столбцами.'.format(name))
            if len(tables) == 1:
                return tables[0]
            return pd.concat([table[first] for table in tables],
                             ignore_index=True, copy=False)
        return self._read_csv(path)


    def load_files(self, paths: List[str], progress_cb=None,
                   sheets_by_path: Optional[Dict[str, List[str]]] = None
                   ) -> Dict[str, object]:
        """Загрузить файлы в фоне; ошибку вернуть на месте файла."""
        results: Dict[str, object] = {}
        lock = threading.Lock()
        total = len(paths)
        done = 0

        def worker(p: str):
            started = time.perf_counter()
            try:
                selected = (sheets_by_path or {}).get(p)
                return p, self.read_any_file(p, selected), time.perf_counter() - started
            except Exception as e:
                return p, e, time.perf_counter() - started

        # Для крупных наборов уменьшаем число одновременных загрузок:
        # каждый поток может держать в памяти целую таблицу.
        total_bytes = sum(os.path.getsize(p) for p in paths if os.path.exists(p))
        max_workers = min(self.max_workers, total or 1)
        if total_bytes >= self.large_file_threshold:
            max_workers = min(2, total or 1)

        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = [ex.submit(worker, p) for p in paths]
            for fut in as_completed(futures):
                p, r, elapsed = fut.result()
                with lock:
                    results[p] = r
                    done += 1
                    if progress_cb:
                        progress_cb(done, total, p, elapsed,
                                    len(r) if isinstance(r, pd.DataFrame) else 0)
        # Порядок файлов в результате совпадает с порядком выбора в окне.
        return {path: results[path] for path in paths}
