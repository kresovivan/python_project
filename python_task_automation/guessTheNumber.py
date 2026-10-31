#Игра в угадывание чисел

"""
1. secretNumber = случайное число от 1 до 20
2. Вывести приветствие
3. Для guessTaken от 1 до 6:
     a. Запросить у игрока число
     b. Если guess < secretNumber → вывести "больше"
     c. Иначе если guess > secretNumber → вывести "меньше"
     d. Иначе → прервать цикл (угадано)
4. Если guess == secretNumber → вывести "Отлично!" + номер попытки
5. Иначе → вывести "Не повезло" + загаданное число
"""

import random

secretNumber = random.randint(1,20)
print("Я загадал число от 1 до 20")

# Игроку дается 6 попыток

for guessTaken in range (1, 7):
    print("Угадайте число")
    guess = int(input())

    if guess < secretNumber:
        print("Я загадал большее число")
    elif guess > secretNumber:
        print("Я загадал меньшее число")
    else:
        break #число угадано!

if guess == secretNumber:
    print("Отлично! Количество попыток: " + str(guessTaken) + "." )
else:
    print("Вам не повезло. Я загадал число " + str(secretNumber))



