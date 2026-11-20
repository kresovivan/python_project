# Ловим ошибки

title = "Программирование для начинающих"
try:
    print(titel)

except (NameError, IndexError) as msg:
    print(msg)
    print(type(msg).__name__, ":", msg)
    print(repr(msg))
