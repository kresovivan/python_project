chars = ["A", "B", "C"]
fruit = ("Apple", "Banana", "Cherry")
info = {"name": "Mike", "ref": "Python", "sys": "Win"}

print("\nЭлементы: \t", end=" ")
for item in chars:
    print(item, end=" ")

print("\nПронумерованные: \t", end=" ")
for item in enumerate(chars):
    print(item, end=" ")


print("\nНЕсколько списков одноврменно: \t", end=" ")
for item in zip(chars, fruit):
    print(item, end=" ")


print("\nПарами ключ - значение:\t", end="\n")
for key, value in info.items():
    print(key, "=", value)
