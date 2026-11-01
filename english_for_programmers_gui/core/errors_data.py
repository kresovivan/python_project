# =============================================================================
# Настоящие сообщения об ошибках Python - для режима "Читаем ошибки"
# =============================================================================

from core.models import ErrorMessage

ERRORS = [
    ErrorMessage(
        message="NameError: name 'eggs' is not defined",
        ru="Ошибка имени: имя 'eggs' не определено",
        words="name - имя, is not defined - не определено",
        hint="Переменную используют до того, как создали, или опечатались в имени.",
    ),
    ErrorMessage(
        message="TypeError: 'str' object does not support item assignment",
        ru="Ошибка типа: объект 'str' (строка) не поддерживает присваивание элементу",
        words="object - объект, does not support - не поддерживает, item - элемент, assignment - присваивание",
        hint="Строку нельзя менять по индексу: name[0] = 'А'. Соберите новую строку.",
    ),
    ErrorMessage(
        message="IndexError: list index out of range",
        ru="Ошибка индекса: индекс списка вне диапазона",
        words="list - список, index - индекс, out of range - вне диапазона",
        hint="Обращаетесь к элементу, которого нет. В списке из 3 элементов индексы 0, 1, 2.",
    ),
    ErrorMessage(
        message="TypeError: tuple expected at most 1 argument, got 3",
        ru="Ошибка типа: tuple ожидал не более 1 аргумента, получено 3",
        words="expected - ожидалось, at most - не более, argument - аргумент, got - получено",
        hint="tuple() и list() принимают один аргумент: tuple(['a', 'b']), а не tuple('a', 'b').",
    ),
    ErrorMessage(
        message="SyntaxError: invalid syntax",
        ru="Синтаксическая ошибка: неверный синтаксис",
        words="invalid - неверный, syntax - синтаксис (правила записи кода)",
        hint="Опечатка в записи: забыли двоеточие, скобку или кавычку.",
    ),
    ErrorMessage(
        message="SyntaxError: unterminated triple-quoted string literal",
        ru="Синтаксическая ошибка: незакрытая строка в тройных кавычках",
        words="unterminated - незавершённый, triple-quoted - в тройных кавычках, string literal - строка",
        hint='Открыли """ и не закрыли. Проверьте, что кавычек три, а не две.',
    ),
    ErrorMessage(
        message="ZeroDivisionError: division by zero",
        ru="Ошибка деления на ноль: деление на ноль",
        words="zero - ноль, division - деление, by - на",
        hint="Где-то делите на 0. Проверьте делитель перед делением.",
    ),
    ErrorMessage(
        message="ModuleNotFoundError: No module named 'requests'",
        ru="Модуль не найден: нет модуля с именем 'requests'",
        words="module - модуль, not found - не найден, named - с именем",
        hint="Модуль не установлен. Установите: pip install requests",
    ),
    ErrorMessage(
        message="ValueError: invalid literal for int() with base 10: 'abc'",
        ru="Ошибка значения: недопустимое значение для int() в десятичной системе: 'abc'",
        words="value - значение, invalid - недопустимый, literal - запись значения, base 10 - десятичная система",
        hint="int() не может превратить буквы в число. Пользователь ввёл не число.",
    ),
    ErrorMessage(
        message="IndentationError: expected an indented block",
        ru="Ошибка отступа: ожидался блок с отступом",
        words="indentation - отступ, expected - ожидался, indented block - блок с отступом",
        hint="После if/for/def со двоеточием следующая строка должна быть с отступом.",
    ),
    ErrorMessage(
        message="AttributeError: 'tuple' object has no attribute 'append'",
        ru="Ошибка атрибута: у объекта 'tuple' нет атрибута 'append'",
        words="attribute - атрибут (свойство или метод), has no - не имеет",
        hint="У этого типа нет такого метода. Кортеж нельзя дополнять - используйте список.",
    ),
    ErrorMessage(
        message="KeyError: 'age'",
        ru="Ошибка ключа: ключа 'age' нет",
        words="key - ключ",
        hint="В словаре нет такого ключа. Проверьте написание или используйте dict.get('age').",
    ),
    ErrorMessage(
        message="TypeError: can only concatenate str (not \"int\") to str",
        ru="Ошибка типа: к строке можно присоединить только строку (не int)",
        words="can only - можно только, concatenate - склеить, not - не",
        hint='Склеиваете строку с числом: "Возраст: " + 5. Нужно str(5) или f-строка.',
    ),
    ErrorMessage(
        message="TypeError: missing 1 required positional argument: 'name'",
        ru="Ошибка типа: не хватает 1 обязательного позиционного аргумента: 'name'",
        words="missing - не хватает, required - обязательный, positional - позиционный",
        hint="Функцию вызвали, не передав ей нужный аргумент.",
    ),
    ErrorMessage(
        message="FileNotFoundError: [Errno 2] No such file or directory: 'data.txt'",
        ru="Файл не найден: нет такого файла или папки: 'data.txt'",
        words="file - файл, not found - не найден, no such - нет такого, directory - папка",
        hint="Неверный путь к файлу или программа запущена из другой папки.",
    ),
    ErrorMessage(
        message="RecursionError: maximum recursion depth exceeded",
        ru="Ошибка рекурсии: превышена максимальная глубина рекурсии",
        words="maximum - максимальный, depth - глубина, exceeded - превышена",
        hint="Функция вызывает сама себя без условия остановки.",
    ),
    ErrorMessage(
        message="UnboundLocalError: cannot access local variable 'x' where it is not associated with a value",
        ru="Ошибка: нельзя обратиться к локальной переменной 'x', у неё ещё нет значения",
        words="cannot access - нельзя обратиться, local - локальный, associated - связан",
        hint="Внутри функции переменную читают до присваивания. Возможно, нужен параметр или global.",
    ),
    ErrorMessage(
        message="ImportError: cannot import name 'foo' from 'bar'",
        ru="Ошибка импорта: нельзя импортировать имя 'foo' из 'bar'",
        words="cannot - нельзя, import - импортировать, from - из",
        hint="В модуле нет такого имени: опечатка или другая версия библиотеки.",
    ),
    ErrorMessage(
        message="PermissionError: [Errno 13] Permission denied: 'report.xlsx'",
        ru="Ошибка доступа: в доступе отказано: 'report.xlsx'",
        words="permission - разрешение, denied - отказано",
        hint="Файл открыт в другой программе (например, Excel) или нет прав на запись.",
    ),
    ErrorMessage(
        message="DeprecationWarning: this function is deprecated and will be removed in a future version",
        ru="Предупреждение об устаревании: функция устарела и будет удалена в будущей версии",
        words="deprecated - устаревший, removed - удалён, future - будущий, version - версия",
        hint="Пока работает, но лучше перейти на новый способ из документации.",
    ),
]
