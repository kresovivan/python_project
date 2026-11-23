"""Общие вспомогательные функции для имён файлов."""

import os


def unique_short_names(names):
    """Короткие имена файлов, уникальные даже при совпадении базовых имён.

    Два файла с одинаковым именем в разных папках иначе дали бы совпадающие
    колонки вида «Файл::поле». Здесь при совпадении добавляется суффикс (_2, _3…).
    """
    short = {}
    for name in names:
        base = os.path.splitext(os.path.basename(name))[0]
        key, suffix = base, 2
        while key in short.values():
            key = f'{base}_{suffix}'
            suffix += 1
        short[name] = key
    return short