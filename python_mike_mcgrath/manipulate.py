"""Обработка строк в Python"""

import inspect


def display(s):
    """Выводит значение аргумента"""
    print(s)


display(print.__name__)
display(print.__doc__)
display(inspect.signature(print))

display(r"C:\Program")
display("C:\\Program")

display("\nHello" + "Python")
display("\\Hello" + "Python")

display("Python in easy steps\n"[7:])
display("P" in "Python")
display("p" in "Python")
