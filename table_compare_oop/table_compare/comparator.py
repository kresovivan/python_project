"""Сопоставление записей по ключу и порядку повторений."""

import os
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .config import (
    KEY_SEP, STATUS_SUFFIX, STATUS_MATCH, STATUS_DIFF, STATUS_MISSING,
    FLAG_COLUMN, FLAG_YES, FLAG_NO,
)


class TableComparator:
    def __init__(self, frames: Dict[str, pd.DataFrame]):
        self.frames = frames

    def compare(self, key_fields: List[str],
                       compare_fields: List[str],
                       extra_fields: Optional[List[str]] = None,
                       progress_cb=None
                       ) -> Tuple[pd.DataFrame, Dict[str, int]]:
        """Векторное сравнение больших таблиц.

        Дубликаты ключей выравниваются по порядковому номеру внутри ключа.
        Выход: таблица значений и статусов, а также общая статистика.
        Сопоставление выполняется средствами pandas без перебора строк.
        """
        frames = self.frames
        extra_fields = extra_fields or []
        if len(frames) < 2:
            raise ValueError("Нужно минимум 2 файла")
        if not key_fields:
            raise ValueError("Не задан ключ")

        names = list(frames.keys())
        short = {n: os.path.splitext(os.path.basename(n))[0] for n in names}
        needed = list(dict.fromkeys(key_fields + compare_fields + extra_fields))
        index_cols = list(key_fields) + ['__occ__']

        if len(names) == 2:
            quick_result = self._compare_unique_keys(
                names, key_fields, compare_fields, extra_fields,
                progress_cb)
            if quick_result is not None:
                return quick_result

        compact: Dict[str, pd.DataFrame] = {}
        index_parts = []
        counts_by_file = {}

        # Читаем/обрабатываем только необходимые столбцы.
        for n in names:
            src = frames[n]
            available = {str(c).strip(): c for c in src.columns}
            missing_keys = [k for k in key_fields if k not in available]
            if missing_keys:
                raise ValueError(
                    "Поле-ключ '{}' отсутствует в файле {}".format(
                        missing_keys[0], os.path.basename(n)))

            d = pd.DataFrame(index=src.index)
            for field in needed:
                d[field] = src[available[field]] if field in available else None

            for k in key_fields:
                d[k] = d[k].astype(str).str.strip()

            d['__occ__'] = d.groupby(
                key_fields, sort=False, dropna=False).cumcount()
            compact[n] = d
            index_parts.append(d[index_cols])

            cnt = d.groupby(key_fields, sort=False, dropna=False).size()
            if not isinstance(cnt.index, pd.MultiIndex):
                cnt.index = pd.MultiIndex.from_arrays([cnt.index], names=key_fields)
            counts_by_file[n] = cnt

        # Полный набор ключ + номер дубля. Все операции ниже выполняются
        # средствами pandas, без прохода Python по каждой записи.
        master = pd.concat(index_parts, ignore_index=True).drop_duplicates(
            subset=index_cols, ignore_index=True)
        master = master.sort_values(index_cols, kind='stable').reset_index(drop=True)

        count_df = pd.concat(counts_by_file, axis=1).fillna(0)
        count_df.columns = names
        present_all = count_df.gt(0).all(axis=1)
        max_count = count_df.max(axis=1)

        # Если ключ отсутствует в одном из файлов, показываем один результат.
        # Если он есть везде, показываем каждый вариант повторяющегося ключа.
        key_meta = count_df.copy()
        key_meta['_present_all'] = present_all
        key_meta['_max_count'] = max_count
        key_meta = key_meta.reset_index()[key_fields + ['_present_all', '_max_count']]
        master = master.merge(key_meta, on=key_fields, how='left', sort=False)
        keep = master['_present_all'] | master['__occ__'].eq(0)
        selected = master.loc[keep, index_cols].reset_index(drop=True)
        selected_index = pd.MultiIndex.from_frame(selected[index_cols])
        key_index = pd.MultiIndex.from_frame(selected[key_fields])

        key_labels = selected[key_fields].astype(str).agg(KEY_SEP.join, axis=1)
        result = pd.DataFrame({
            'Ключ': key_labels.to_numpy(),
            FLAG_COLUMN: np.full(len(selected), '', dtype=object),
        })

        compare_arrays: Dict[str, List[np.ndarray]] = {
            f: [] for f in compare_fields
        }
        stat = {STATUS_MATCH: 0, STATUS_DIFF: 0, STATUS_MISSING: 0}

        for n in names:
            d = compact[n].set_index(index_cols, drop=False)
            sa = d.reindex(selected_index)
            occurrence_present = sa['__occ__'].notna().to_numpy()

            # Ключ выводится, если сам ключ есть в файле, даже если для данного
            # номера повторения строки уже нет.
            key_counts = counts_by_file[n]
            key_present = key_counts.reindex(key_index).fillna(0).to_numpy() > 0
            result[f'{short[n]}::ключ'] = np.where(
                key_present, key_labels.to_numpy(dtype=object), None)

            # Значения последней строки каждого ключа нужны для недостающих
            # вариантов повторяющегося ключа.
            last_values = {}
            for f in list(extra_fields) + list(compare_fields):
                if f not in d.columns:
                    last_values[f] = None
                    continue
                last = compact[n].groupby(
                    key_fields, sort=False, dropna=False)[f].last()
                if not isinstance(last.index, pd.MultiIndex):
                    last.index = pd.MultiIndex.from_arrays(
                        [last.index], names=key_fields)
                last_values[f] = last.reindex(key_index).to_numpy(dtype=object)

            for f in extra_fields:
                arr = sa[f].to_numpy(dtype=object)
                arr[pd.isna(arr)] = ''
                missing_occ = ~occurrence_present
                if last_values[f] is not None:
                    arr[missing_occ & key_present] = last_values[f][missing_occ & key_present]
                arr[~key_present] = None
                arr = np.array([
                    None if v is None else '' if pd.isna(v) else str(v)
                    for v in arr
                ], dtype=object)
                result[f'{short[n]}::{f}'] = arr

            for f in compare_fields:
                arr = sa[f].to_numpy(dtype=object)
                arr[pd.isna(arr)] = ''
                missing_occ = ~occurrence_present
                if last_values[f] is not None:
                    arr[missing_occ & key_present] = last_values[f][missing_occ & key_present]
                arr[~key_present] = None
                arr = np.array([
                    None if v is None else '' if pd.isna(v) else str(v)
                    for v in arr
                ], dtype=object)
                compare_arrays[f].append(arr)
                result[f'{short[n]}::{f}'] = arr

        # Статусы по каждому полю - векторно.
        any_missing = np.zeros(len(result), dtype=bool)
        any_diff = np.zeros(len(result), dtype=bool)

        for f in compare_fields:
            arr = np.vstack(compare_arrays[f])
            missing = np.equal(arr, None).any(axis=0)
            diff = np.zeros(len(result), dtype=bool)
            for i in range(1, arr.shape[0]):
                diff |= (arr[i] != arr[0])
            diff &= ~missing

            status = np.full(len(result), STATUS_MATCH, dtype=object)
            status[missing] = STATUS_MISSING
            status[~missing & diff] = STATUS_DIFF
            result[f'{f}{STATUS_SUFFIX}'] = status
            any_missing |= missing
            any_diff |= (~missing & diff)

        if compare_fields:
            result[FLAG_COLUMN] = np.where(
                any_missing | any_diff, FLAG_YES, FLAG_NO)
            stat[STATUS_MISSING] = int(any_missing.sum())
            stat[STATUS_DIFF] = int((~any_missing & any_diff).sum())
            stat[STATUS_MATCH] = int((~any_missing & ~any_diff).sum())

        ordered = ['Ключ', FLAG_COLUMN]
        ordered += [f'{short[n]}::ключ' for n in names]
        ordered += [f'{short[n]}::{f}' for f in extra_fields for n in names]
        ordered += [f'{short[n]}::{f}' for f in compare_fields for n in names]
        ordered += [f'{f}{STATUS_SUFFIX}' for f in compare_fields]
        result = result[ordered]

        if progress_cb:
            progress_cb(len(result), len(result))
        return result, stat

    def _compare_unique_keys(self, names, key_fields, compare_fields,
                             extra_fields, progress_cb):
        """Сравнить два файла без группировок, если ключи не повторяются."""
        keys = []
        key_parts = []
        columns = []
        for name in names:
            source = self.frames[name]
            available = {str(col).strip(): col for col in source.columns}
            missing_keys = [field for field in key_fields if field not in available]
            if missing_keys:
                raise ValueError(
                    "Поле-ключ '{}' отсутствует в файле {}".format(
                        missing_keys[0], os.path.basename(name)))
            parts = {field: source[available[field]].astype(str)
                     .str.strip().to_numpy(dtype=object)
                     for field in key_fields}
            if len(key_fields) == 1:
                key = pd.Index(parts[key_fields[0]])
            else:
                key = pd.MultiIndex.from_arrays(
                    [parts[field] for field in key_fields], names=key_fields)
            if not key.is_unique:
                return None
            keys.append(key)
            key_parts.append(parts)
            columns.append(available)

        all_keys = keys[0].union(keys[1], sort=None)
        if len(key_fields) == 1:
            labels = all_keys.to_numpy(dtype=object)
        else:
            label_index = all_keys.get_level_values(0)
            for part_index in range(1, len(key_fields)):
                label_index = label_index.str.cat(
                    all_keys.get_level_values(part_index), sep=KEY_SEP)
            labels = label_index.to_numpy(dtype=object)
        positions = [key.get_indexer(all_keys) for key in keys]
        present = [indexer >= 0 for indexer in positions]
        missing = ~(present[0] & present[1])
        shorts = [os.path.splitext(os.path.basename(name))[0]
                  for name in names]

        result = pd.DataFrame({
            'Ключ': labels,
            FLAG_COLUMN: np.full(len(labels), '', dtype=object),
        })
        for index, short in enumerate(shorts):
            result[f'{short}::ключ'] = np.where(present[index], labels, None)

        any_diff = np.zeros(len(labels), dtype=bool)
        for field in list(extra_fields) + list(compare_fields):
            values = []
            for index, name in enumerate(names):
                source = self.frames[name]
                column = columns[index].get(field)
                if field in key_parts[index]:
                    original = key_parts[index][field]
                elif column is None:
                    original = np.full(len(source), '', dtype=object)
                else:
                    original = source[column].fillna('').astype(str).to_numpy()
                aligned = np.empty(len(labels), dtype=object)
                aligned[:] = None
                aligned[present[index]] = original[positions[index][present[index]]]
                values.append(aligned)
                result[f'{shorts[index]}::{field}'] = aligned
            if field in compare_fields:
                diff = present[0] & present[1] & (values[0] != values[1])
                any_diff |= diff
                status = np.full(len(labels), STATUS_MATCH, dtype=object)
                status[missing] = STATUS_MISSING
                status[diff] = STATUS_DIFF
                result[f'{field}{STATUS_SUFFIX}'] = status

        stat = {STATUS_MATCH: 0, STATUS_DIFF: 0, STATUS_MISSING: 0}
        if compare_fields:
            result[FLAG_COLUMN] = np.where(
                missing | any_diff, FLAG_YES, FLAG_NO)
            stat[STATUS_MISSING] = int(missing.sum())
            stat[STATUS_DIFF] = int(any_diff.sum())
            stat[STATUS_MATCH] = len(labels) - stat[STATUS_MISSING] - stat[STATUS_DIFF]

        ordered = ['Ключ', FLAG_COLUMN]
        ordered += [f'{short}::ключ' for short in shorts]
        ordered += [f'{short}::{field}' for field in extra_fields for short in shorts]
        ordered += [f'{short}::{field}' for field in compare_fields for short in shorts]
        ordered += [f'{field}{STATUS_SUFFIX}' for field in compare_fields]
        if progress_cb:
            progress_cb(len(result), len(result))
        return result[ordered], stat
