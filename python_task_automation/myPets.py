myPets = ["Софи", "Питер", "Толстяк", "Кисунчик"]
print("Укажите имя домашнего питомца:")
name = input()
if name not in myPets:
    print("У меня нет домашнего питомца по имени " + name)
else:
    print(name + " - мой питомец")