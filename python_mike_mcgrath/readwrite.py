"""
Отрывок из баллады Редингской тюрьмы
"""

poem = "Нет, не смотрел никто из нас\n"
poem += "НС такой таской в глазах\n"
poem += "На лоскуток платка\n"
poem += "В тюремных небесах\n"

file = open("poem.txt", "w")

file.write(poem)
file.close()
file = open("poem.txt", "r")

for line in file:
    print(line, end="")
file.close()

file = open("poem.txt", "a")
file.write("Оскар Уайльд")
file.close()
