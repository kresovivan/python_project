#Отметка
print("Введи число: ", end = " ")
Score = int(input())
print("Это ", end = " ")
if (Score) > 100 or (Score) < 0 :
    print("Неправильно(0)")
if (Score) >= 0 and (Score) < 25 :
    print("Ужасно (6)")
if (Score) >= 25 and (Score) < 45 :
    print("Плохо (5)")
if (Score) >= 45 and (Score) < 65 :
    print("Сойдет(4)")
if (Score) >= 65 and (Score) < 80 :
    print("Средне(3)")
if (Score) >= 80 and (Score) < 90 :
    print("Хорошо(2)")
if (Score) >= 90 and (Score) <= 100 :
    print("Очень хорошо (1)")