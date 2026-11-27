"""Можно изучить имена функций в модуле"""

import dog

for i in dir(dog):
    print(i)

print(dir(__builtins__))


snack = "{} and {}".format("Бургер", "Картошка фри")
print("\nЗамены: ", snack)

snack = "{1} and {0}".format("Бургер", "Картошка фри")
print("\nЗамены: ", snack)


snack = "%s and %s" % ("Молоко", "Печенье")
print("\nЗамены: ", snack)
