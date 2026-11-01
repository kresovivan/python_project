supplies = ["ручки", "карандаши", "степлеры", "скоросшиватели"]
for index, item in enumerate(supplies):
    print("Индекс " + str(index) + ": " + item)


import random

cat = ["Толстый", "Серый", "Громкий"]

result = random.choice(cat)
print(result)

import random  # Подключаем модуль random

cat = ["Толстый", "Серый", "Громкий"]

random.shuffle(cat)  # Меняем порядок элементов случайным образом
print(cat)  # Выводим изменённый список
