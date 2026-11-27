"""Изменение строк"""

string = "coding for beginners in easy steps"

print("Заглавная буква:\n", string.capitalize())
print()
print("Заглавные буквы в каждом слове:\n", string.title())
print("\nПо центру: ", string.center(40, "*"))

print("\nВерхний регистр: ", string.upper())
print("\nС соединением: ", string.join("**"))
print("\nСоединение слов через *:", "*".join(string.split()))
print("\nС заменой: ", string.replace("s", "$"))
