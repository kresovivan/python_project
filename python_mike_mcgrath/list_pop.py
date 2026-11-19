# Изменение списков

basket = [" Яблоко ", " Булочка ", " Кола "]
crate = [" Яйцо ", " Инжир ", " Виноград "]
print("Список basket: ", basket)
print("Элементов в списке basket: ", len(basket))

basket.append("Чернослив")
print("Добавлено: ", basket)
print("Последний удаленный элемент: ", basket.pop())
print("Список Basket: ", basket)


basket.extend(crate)
print("Добавлено: ", basket)
del basket[1]
print("C удаленным элементом", basket)
del basket[1:3]
print("C удаленным срезом", basket)
list.count(basket)
