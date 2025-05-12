print("Введи число:   ", end="")
Score = int(input())
print("Это ", end="")
if 0 <= Score < 25:
    print("Ужасно (6)")
if 25 <= Score < 45:
    print("Плохо (5)")
if 45 <= Score < 65:
    print("Сойдет(4)")
if 65 <= Score < 80:
    print("Средне(3)")
if 80 <= Score < 90:
    print("Хорошо(2)")
if 90 <= Score <= 100:
    print("Очень хорошо (1)")
if Score > 100:
    print("Неправильно(0)")