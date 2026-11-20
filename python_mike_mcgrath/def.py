# Объявление фукнции

"""Главное правило (LEGB)
Python ищет имя в четырёх местах по порядку:
Local — внутри функции
Enclosing — во внешней функции (для вложенных)
Global — на уровне модуля
Built-in — встроенные (len, print, ...)
Побеждает первое найденное сверху вниз."""

global_var = 1


def my_vars():
    print("Глобальная переменная:", global_var)
    local_var = 2
    print("Локальная переменная:", local_var)
    global inner_var
    inner_var = 3
    print("Вторая глобальная переменная:", inner_var)


my_vars()
