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

## Остальные проекты

| Папка | Что это |
|---|---|
| english_for_programmers/ | консольная версия тренажёра |
| table_compare_oop/ | сравнение таблиц CSV/Excel по общему ключу (GUI на Tkinter, ООП, векторное сопоставление) — см. [table_compare_oop/README.md](table_compare_oop/README.md) |
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
