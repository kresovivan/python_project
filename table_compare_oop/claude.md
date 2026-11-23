# CLAUDE.md — guide for AI assistants working on this repo

Настольное приложение на Python/Tkinter для сравнения двух и более таблиц
(CSV / Excel) по выбранному ключу.

## Стек

- Python 3.10+, Tkinter, `unittest` (без pytest).
- Зависимости: `numpy`, `pandas>=2.0`, `chardet`, `openpyxl`, `xlrd`
  (см. `requirements.txt` и `pyproject.toml`).

## Команды

```powershell
# установка (зависимости)
py -m pip install -r requirements.txt

# запуск приложения
py run.py
# или, если проект установлен как пакет:
table-compare

# тесты (корень проекта)
py -m unittest tests.test_all_functions -v          # все функции
py -m unittest discover -s tests -v                 # весь набор
```

## Структура (все слои — классы, ООП)

- `table_compare/loader.py` — `TableLoader`: чтение CSV/Excel, автодетект
  кодировки и разделителя, выбор листов Excel, параллельная загрузка, `list_sheets`.
- `table_compare/comparator.py` — `TableComparator`: векторное сопоставление по
  ключу, дубли ключа по порядку повторений. Ускоренный путь `_compare_unique_keys()`
  для двух файлов с уникальным ключом; общий путь для дублей и 3+ файлов.
- `table_compare/statistics.py` — `StatisticsAnalyzer`: показатели по полям и файлам.
- `table_compare/exporter.py` — `ReportExporter`: выгрузка CSV / XLSX / HTML;
  при >1 048 575 строк XLSX делится на листы «Результаты N».
- `table_compare/naming.py` — `unique_short_names()`: уникальные короткие имена
  файлов (защита от коллизии `Файл::поле`).
- `table_compare/ui/` — `MainWindow`, `HelpWindow`, `Theme`, `CardFrame`.

## Ключевые соглашения

- Статусы и имена колонок заданы в `table_compare/config.py`
  (`STATUS_MATCH/DIFF/MISSING`, `STATUS_SUFFIX = '::статус_сверки'`, `FLAG_COLUMN`).
  Меняя их, обновляйте `statistics.py`, `exporter.py`, `main_window.py` и тесты.
- **Отсутствующие значения в `result_df` — это `None`, а не `nan`.** pandas 3.x
  превращает `None` в `NaN` при присвоении в столбец numpy-массива объектного типа,
  поэтому `TableComparator._finalize()` возвращает явные `None`. Не убирайте её.
- Значения конвертируются **векторизованно**: склейка ключа через `Series.str.cat`,
  приведение типов через `np.where(np.equal(arr, None), None, np.where(pd.isna(arr), '', arr.astype(str)))`.
  Не вводите построчные Python-циклы по ячейкам на этих участках.
- `to_numpy(dtype=object, copy=True)` — обязательно `copy=True`, если дальше идёт
  запись в массив (`arr[...] = ...`), иначе возможен read-only в pandas 3.x.
- Длительные операции (загрузка, сравнение, экспорт) — в фоновых потоках; в GUI —
  только через `self._post(...)`. `self.load_metrics` защищён `self._load_metrics_lock`.
- Просмотр показывает первые `PREVIEW_MAX_ROWS` (5000); фильтр «только расхождения»,
  поиск и сортировка действуют на представление через `_filtered_view()` /
  `_render_tree()`. Экспорт всегда содержит весь результат (или подмножество
  расхождений через `_discrepancy_view()`).

## Тестовые данные

`examples/test_A.csv` (запятая) и `examples/test_B.csv` (`;`) — компактный набор,
покрывающий дубли ключа, отсутствующие записи, отличия, пробелы в ключе и
автодетект разделителя. Ожидаемый итог: Совпадает 5 / Отличается 3 / Нет строки 2.

## Требования к правкам

1. Сохраняйте ООП-структуру и публичные имена методов.
2. После изменений запускайте `unittest` и следите, что «отсутствие» остаётся `None`.
3. UI-текст и комментарии — по-русски; код — по общему стилю (PEP 8).
4. Пользовательская документация — в `MANUAL.md`; обновляйте её при изменении видимой функциональности.