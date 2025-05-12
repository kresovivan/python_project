#Отметка
print("Введи число: ", end=" ")
Score = int(input())
print("Это ", end=" ")
if Score > 100 or Score < 0:
    print("Неправильно(0)")
elif Score >= 90:
    print("Очень хорошо (1)")
elif Score >= 80:
    print("Хорошо(2)")
elif Score >= 65:
    print("Средне(3)")
elif Score >= 45:
    print("Сойдет(4)")
elif Score >= 25:
    print("Плохо(5)")
else:
    print("Ужасно (6)")