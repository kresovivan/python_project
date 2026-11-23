# python_project

Учебный репозиторий по Python: тренажёр английского и китайского, учебные скрипты по книгам и небольшие проекты.

## Главный проект

**english_for_programmers_gui** — тренажёр английского и китайского для программистов (GUI на CustomTkinter). Подробное описание — в `english_for_programmers_gui/README.md`.

Запуск:

```text
cd english_for_programmers_gui
python main.py
```

Зависимости:

```text
pip install -r english_for_programmers_gui/requirements.txt
```

## Сравнение таблиц CSV / Excel (`table_compare_oop`)

Настольное приложение на Tkinter для сверки двух и более выгрузок (CSV, XLSX, XLS)
по общему ключу. Код написан в объектно-ориентированном стиле, сопоставление — векторное.

Возможности:

- автоопределение кодировки и разделителя CSV;
- загрузка нескольких листов Excel;
- одиночный или составной ключ, корректная обработка дублей ключа и пробелов по краям;
- цветная таблица результатов, плитки-итоги, фильтр «Только расхождения», поиск и сортировка;
- копирование в буфер обмена (TSV);
- экспорт в XLSX / CSV / HTML, включая «только расхождения»; разбиение больших XLSX на листы.

Запуск:

```text
cd table_compare_oop
py -m pip install -r requirements.txt
py run.py
```

Тесты:

```text
cd table_compare_oop
py -m unittest discover -s tests -v
```

Подробнее — [table_compare_oop/README.md](table_compare_oop/README.md) и [инструкция пользователя](table_compare_oop/MANUAL.md).

## Настольный питомец Кисунчик (`kisunchik_pet`)

Рыже-белый котик на рабочем столе Windows: машет лапкой, кувыркается, ест рыбку
и сам гуляет по всем мониторам. Помогает учить английский — показывает слова
с переводом и произносит их голосом: офлайн SAPI Windows (Zira, en-US) в пяти
характерах или онлайн Google TTS с выбором акцента. Словарь 4110 слов из
`english_for_programmers_gui` разбит на 21 блок, ведётся дневник прогресса (`progress.json`).

Запуск:

```text
cd kisunchik_pet
pythonw run.py
```

Тесты (88 штук):

```text
cd kisunchik_pet
python -m unittest discover -s tests -t .
```

Подробнее — [kisunchik_pet/README.md](kisunchik_pet/README.md).

## Остальные проекты

| Папка | Что это |
|---|---|
| english_for_programmers/ | консольная версия тренажёра |
| table_compare_oop/ | сравнение таблиц CSV/Excel — см. раздел «Сравнение таблиц» |
| kisunchik_pet/ | настольный питомец и тренажёр английского — см. раздел «Настольный питомец» |
| python_mike_mcgrath/ | упражнения из книги (функции, циклы, исключения) |
| python_task_automation/ | упражнения «Автоматизация рутинных задач» |
| config_dump_parser/ | парсер конфигураций 1С |
| webapp/ | веб-упражнения |

## Тесты

В `english_for_programmers_gui`:

```text
python -m unittest discover -s tests -t .
```

Быстрые тесты логики:

```text
python -m unittest discover -s tests/unit -t .
```

В `table_compare_oop`:

```text
cd table_compare_oop
python -m unittest discover -s tests -v
```

В `kisunchik_pet`:

```text
cd kisunchik_pet
python -m unittest discover -s tests -t .
```
