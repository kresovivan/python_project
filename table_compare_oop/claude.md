# CLAUDE.md — guide for AI assistants working on this repo

Настольное приложение на Python/Tkinter для сравнения двух и более таблиц
(CSV / Excel) по выбранному ключу.

## Стек

- Python 3.10+, Tkinter (входит в Windows), pytest не используется — `unittest`.
- Зависимости: `numpy`, `pandas>=2.0`, `chardet`, `openpyxl`, `xlrd`
  (см. `requirements.txt`).

## Команды

```powershell
# установка
py -m pip install -r requirements.txt

# запуск приложения
py run.py

# тесты (корень проекта)
py -m unittest discover -s tests -v
```

## Структура (все слои — классы, ООП)

- `table_compare/loader.py` — `TableLoader`: чтение CSV/Excel, автодетект
  кодировки и разделителя, выбор листов Excel, загрузка в фоне.
- `table_compare/comparator.py` — `TableComparator`: векторное сопоставление по
  ключу, обработка дублей ключа по порядку повторений. Есть ускоренный путь
  `_compare_unique_keys()` для двух файлов с уникальным ключом.
- `table_compare/statistics.py` — `StatisticsAnalyzer`: показатели по полям и файлам.
- `table_compare/exporter.py` — `ReportExporter`: выгрузка CSV / XLSX / HTML;
  при >1 048 575 строк XLSX делится на листы «Результаты N».
- `table_compare/ui/` — `MainWindow`, `HelpWindow`, `Theme`, `CardFrame`.

## Ключевые соглашения

- Статусы и имена колонок заданы в `table_compare/config.py`
  (`STATUS_MATCH/DIFF/MISSING`, `STATUS_SUFFIX = '::статус_сверки'`,
  `FLAG_COLUMN` и т.д.). Меняя их, обновляйте `statistics.py`, `exporter.py`,
  `main_window.py` и тесты.
- **Отсутствующие значения в `result_df` должны быть `None`**, а не `nan`.
  В pandas 3.x присвоение numpy-массива объектного типа в столбец превращает
  `None` в `NaN`; для этого в `comparator.py` есть нормализация
  `TableComparator._finalize()`. Не убирайте её и не присваивайте сырые
  numpy-массивы с `None` напрямую в `result`.
- Изменяемые numpy-массивы, полученные через `.to_numpy(dtype=object)`,
  делайте с `copy=True`, если планируется запись (`arr[...] = ...`) — иначе
  возможен `read-only` в pandas 3.x.
- Весь длительный код (загрузка, сравнение, экспорт) выполняется в фоновых
  потоках и передаёт результат в UI через `self._post(...)`.
- UI показывает первые `PREVIEW_MAX_ROWS` (5000) строк; экспорт содержит всё.

## Требования к правкам

1. Сохраняйте ООП-структуру и существующие имена публичных методов.
2. После изменений запускайте `unittest` и проверяйте, что «отсутствие» остаётся `None`.
3. Кириллицу в UI оставляйте на русском; комментарии/док-строки — по-русски, код — по общим правилам.