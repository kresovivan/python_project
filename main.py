#1.Списки List#
from msilib import change_sequence

#Инициализация списка переменными
my_list1=['one','two']
my_list2 = list(['one','two'])
#Добавление в список осуществляется через вызов у него метода append(val), где vak -добавляемое в окнец
#списка значение
my_list = list(['one','two'])
print(my_list)
my_list.append('three')
my_list.append('4')
my_list.append('5')
print(my_list)

my_new_list: list[int] = [4,5]
my_new_list.append(1043)
print(my_new_list)

#Добавление объекта в список на указанную позицию.
names = ['Max','Tom','Alex']
print(names)
names.insert(0,'John')
names.insert(0,'Ivan')
print(names)

#Удаление элемента из списка
names.remove('Ivan')
print(names)

#Сортировка списка
names.sort()
print(names)

#Посчитать сколько раз по значению повторяется элемент
my_list=[1,2,3,2,2,2,5,5,]
print(my_list.count(5))

#Присваивание списка новой переменной (копирование самого списка не выполняется)
my_array = [1,2,3,5,7,8,10]
print(my_array)
my_new_array = my_array
my_new_array.append(12)
print(my_array)

#Работа с копией существующего списка через новую переменную во избежание изменений исходного списка
#необходимо использовать метод copy()

my_array = [2,3,5,7,8,10]
print(my_array)
my_new_array = my_array.copy()
my_new_array.append(200)
print(my_array)
print(my_new_array)


# проверить, содержится ли в последовательности (списке, строке и т.д.) объект с
# определенным значением, можно следующим способом
my_array = [2,3,4,5,8,10]
print(2 in my_array)
print(0 in my_array)

#2.Множества set#
#Добавления элементов#
my_list = [0,1,1,2,3,9,4,5,6,6,7,8,9]
my_set = set() #пустое множество
my_set = set(my_list)
my_set = {0,1,1,2,3,9,4,5,6,6,7,8,100}
print(my_set)

#Изменение множества#
my_set.add(102)
print(my_set)
my_set.update([2,100,99,4,5,6,2030])
print(my_set)

#Удаление элементов#
my_set.remove(2)
print(my_set)
my_set.discard(100)
print(my_set)

#Операции над множествами
A = {0,1,2,3,4}
B = {1,3,5,6,7}
#Объединение
new_set = A | B
print(new_set)
#Пересечение
new_set = A & B
print(new_set)
#симметрическая разность
new_set = A ^ B
print(new_set)
#разность A - B
new_set = B - A
print(new_set)

#Проверка на то является ли множество A подмножеством B и наоборот выполняется следующим образом
A = {1,2,3}
B = {1,2,3,4}
#A является подмножеством B#
print(A.issubset(B))
#B является надмножеством A#
print(B.issuperset(A))
A.add(5)
print(A)

#3.Словари dictionary, неупорядоченные коллекции#

my_dict = { } #Пустой словарь
my_dict = {'name': 'Alex', 'course': 3}
#Вложение
my_dict = {'info': {'name':'Alex', 'course': 3}}
print('info' in my_dict)

#вывести все ключи
print(list(my_dict.keys()))
#вывести все значения
print(list(my_dict.values()))
#вывести коретжи пар ключ:значение
print(list(my_dict.items()))
#копировать словарь можно следующим образом
my_dict = {'name': 'Alex', 'course': 3}
my_new_dict = my_dict.copy()
my_new_dict.update({'info': 'None'})
print(my_dict)
print(my_new_dict)
my_dict = {'name':'Alex', 'course': 3, 'info':{'age':21,'country': 'rus'}}
print(my_dict)
my_new_dict = my_dict.copy()
my_new_dict['info']['age'] = 1
print(my_dict) #Изменились значения в исходном словаре, чтобы такого не было нужно использовать#
# глубокое копирование#

import copy
my_dict = {'name':'Alex', 'course': 3, 'info':{'age':21,'country': 'rus'}}
my_new_dict = copy.deepcopy(my_dict)
my_new_dict['info']['age'] = 1
print(my_new_dict)
print(my_dict) #первоисточник не изменился

#Условный оператор if#
t = 29
if t >= 30:
    print('Надеть шорты')
else:
    print('Надеть брюки')

#Вложенный if
value = 9
if value > 30:
    if value < 50:
        print('30 < value < 50')
    else:
        print('30 < value >=50')
else:
    if value > 10:
        print('30 >= value > 10')
    else:
        print('30 >= value < 10')
#Когда необходимо указать, что в блоке if ничего не выполняется, используется команда pass

a = 20
if a < 25:
    pass
else:
    a = 25
print(a)

A=50
Z=20
B=20
C=20
#Тернарный оператор
if A:
    Z=B
else:
    Z=C
#это можно представить ввиде:
Z=B if A else C
a = 300
b = 20
max_value = a if a > b else b
print(max_value)


value = 2
match value:
    case 2:
        print('2')
        print(f'{value} + 2 = {value + 2}')
    case 4:
        print('4')
    case _:
        print('8')


#Циклы и while и операторы break, continue, pass
#from multiprocessing import Pool
#from multiprocessing import Pool
##
# def process_range(start, end):
#     """Функция для обработки диапазона чисел."""
#     result = []
#     for x in range(start, end):
#         result.append(x)  # Вместо вывода на экран сохраняем числа в список
#     return result
#
# if __name__ == "__main__":
#     y = 9000  # Конечное число
#     num_processes = 30  # Количество процессов
#     chunk_size = y // num_processes  # Размер диапазона для каждого процесса
#
#     # Создаем список диапазонов для каждого процесса
#     ranges = [(i * chunk_size, (i + 1) * chunk_size) for i in range(num_processes)]
#     ranges[-1] = (ranges[-1][0], y)  # Убедимся, что последний диапазон включает остаток
#
#     # Используем Pool для параллельной обработки
#     with Pool(processes=num_processes) as pool:
#         results = pool.starmap(process_range, ranges)
#
#     # Объединяем результаты (если нужно)
#     final_result = []
#     for result in results:
#         final_result.extend(result)

##    print("Обработка завершена")##

x=0
y=5
while x < y:
    print(x, end=' ')
    x +=1
else:
    print('Happy End!')


#Оператор continue, позволяет пропускать оставшуюся часть, которую не нужно проверять и переводить программу в начало цикла

import time
start_time = time.time()  # Засекаем начальное время

x = 0

while x < 800:
    x += 1
    if x % 2 == 0:  # Проверяем, является ли число четным
        continue  # Пропускаем оставшуюся часть цикла для четных чисел
    print(f"Нечетное число: {x}")

end_time = time.time()  # Засекаем конечное время
execution_time = end_time - start_time  # Вычисляем время выполнения
print(f"Код выполнился за {execution_time:.4f} секунд")

#Оператор Break
#Он используется для немедленного выхода из цикла

x = 0

while x < 60000000:
    x += 1
    if x == 50000:
        print("Достигнуто число 5. Выход из цикла.")
        break  # Прерываем цикл
    print(f"Текущее число: {x}")
print("Цикл завершён.")


#Цикл for

for it in('first', 'second', 4, 5.9, 'finish'):
    print(it)

my_tuple_list = [(3,6), (0,1), (4,5), ('O',3.9)]
for (a,b) in my_tuple_list:
    print(a,b, end=' ')

#Списковые включения

my_list = [1.25, -9,10,3.78,-5.92, -1.16, 80]
new_list = [i if i > 0 else -1000 for i in my_list]
print(new_list)


#Передача объектов в функцию

def test(a,b,c):
    print('a = {}; b = {}; c = {}'.format(a,b,c))

x,y,z = (5, [1,4], 'Str')
test(x,y,z)
print('x = {}; y = {}; z = {}'.format(x,y,z))

#Проверим, что в качестве аргументов функции, в случае ее вызова, аргументам присваиваются ссылки
#на объекты из вызывающей области
def test(a,b,c):
    print('a = {}; b = {}; c = {}'.format(id(a),id(b),id(c)))

x,y,z = (5, [1,4], 'Str')
test(x,y,z)
print('x = {}; y = {}; z = {}'.format(id(x),id(y),id(z)))

