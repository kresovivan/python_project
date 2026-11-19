# Проверка условия в коде на истинность. Принимает булево значение True или False

num = int(input("Введите число: "))
if num > 5:
    print("Число больше 5")
elif num < 5:
    print("Число меньше 5")
else:
    print("Число равно 5")

if num > 7 and num < 9:
    print("Число равно 8")
if num == 1 or num == 3:
    print("Число равно 1 или 3")
