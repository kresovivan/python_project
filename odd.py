
from datetime import datetime
"""
Думайте о модулях как о коллекциях связанных функций
"""

odds = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19,
        21, 23, 25, 27, 29, 31, 33, 35, 37, 39,
        41, 43, 45, 47, 49, 51, 53, 55, 57, 59]

right_this_minute = datetime.today().minute
print(right_this_minute)
"""
1.datetime - это класс (модуль)
2.datetime.today() - это метод класса
3.Сначала вызывается datetime.today() → создает объект с текущим временем
Затем у этого объекта берется атрибут .minute
В итоге получаем число (int) - текущую минуту
"""
if right_this_minute in odds:
    print("This minute seems a little odd.")
else:
    print("Not an odd minute.")
    
from os import getcwd
where_am_i = getcwd()
print(where_am_i) #PS C:\Users\Kresov Ivan\PycharmProjects\PythonProject> 

import sys
import os
print(sys.platform) #win32 - обозначает семейство Windows, а не разрядность
print(sys.version) #3.14.0 (tags/v3.14.0:ebf955d, Oct  7 2025, 10:15:03) [MSC v.1944 64 bit (AMD64)]
print(os.getcwd()) #C:\Users\Kresov Ivan\PycharmProjects\PythonProject
#print(os.listdir()) #['odd.py', 'odd.pyc', 'README.md']
#print(os.environ)
print(os.getenv('Path'))

import datetime
print(datetime.date.today()) #2026-02-24
print(datetime.date.today().day) #24
print(datetime.date.today().month) #2
print(datetime.date.today().year) #2026
print (datetime.date.isoformat(datetime.date.today())) #2026-02-24 дата в виде строки


import time
print(time.strftime("%I:%M")) #12:09
print(time.strftime("%A:%p")) #Tuesday:AM

"""
В качестве примера фнкциональных возможностей стандартной библиотеки представьте, что у вас есть некоторые 
HTML документы, и вы беспокоитесь, что они могут содержать потенциоально опасные теги <script>
Вместо того, чтобы просматривать разметку HTML и удалять теги, почему бы не экранировать проблемные
угловые скобки с помощью фннкции escape из модуля html?
"""

import html
print(html.escape('This HTML fragment contains a <script>alert("boo!")</script>')) 
#This HTML fragment contains a &lt;script&gt;alert(&quot;boo!&quot;)&lt;/script&gt;
print(html.unescape("I &hearts; Python's &lt;script&gt;alert(&quot;boo!&quot;)&lt;/script&gt"))

"""
Значения переменным в Python присваиваются динамически.
Их типы не требуют предвариательного определения.
Переменные принимают теже типы, что имеют объекты, которые им присваиваются.
В нашей программе переменной odds присваивается список целых чисел,
поэтому odds в этом случае становится списком.

Вызов метода возвращает результат
Говорить о вызове метода позволяют стандартные постфиксные круглые скобки ()
Вызов today() возвращает объект времени, содержащий информацию о текущем времени,
раздробленную на части.
Это обычные атрибуты текущего времени, обратиться к которым можно с помощью 
знака точки (.)
Нас интересует атрибут минуты, к нему можно обратиться добавив .minute к вызову
метода.
Полученное значение присваивается переменной right_this_minute.
Можно думать об этой строчке кода рассуждая таким образом: 
Создается объект, представляющий текущее время, из него извлекается
значение атрибута minute, которое затем присваивается переменной. 
"""
from datetime import datetime
odds = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19,
        21, 23, 25, 27, 29, 31, 33, 35, 37, 39,
        41, 43, 45, 47, 49, 51, 53, 55, 57, 59]

"""Здесь создается перемення right_this_minute и ей присваивается значение
right_this_minute = datetime.today().minute #Этот вызов генерирует значение присваеваемой переменной"""


"""Инструкция if определяет истинность или ложность выражения."""
if right_this_minute in odds: #Оператор in может определеить находится ли одна сущность внутри другой
    print("This minute seems a little odd.")
else:
    print("Not an odd minute.")
"""Оператор in вовзаращает True или False
#Если значение right_this_minute  содержится в odds, выражение в инструкции if вернут True,
#И она выполнит ассоциированный с ней блок кода"""
    
"""
Заманчиво разделить одну строчку на две, чтобы сделать ее проще для понимания
"""
from datetime import datetime
time_now = datetime.today()
right_this_minute = time_now.minute
print(right_this_minute)

"""
Двоеточие очень важно, поскольку вводит
новый блок кода, который должен быть смещен на один отступ вправо.
Если вы забыли сделать отступ, то интерпретатор выведет ошибку.
Не только инструкция if в данном примере содержит двоеточие,
его также имеет else. 

Как варианты может иметь if
else - блок кода который выполняется, когда условное выражение в инструкции if
возвращает значение false.
Если есть несколько условий, то можно исползовать elif - кажду со своим собственным блоком кода.
"""
today = datetime.today().strftime("%A")
print(today)
if today == 'Saturday':
    print("Party!!!")
elif today == 'Sunday':
    print("Recover")
else:
    print("Work, work,work")
    
"""
Важно понимать, что Python отступы используются для отделения блоков кода.
Отступы это единственный механизм группировки кода, который представляет Python
"""
condition = 'Headache'
if today == 'Saturday':
    print("Party!!!")
elif today == 'Sunday':
    if condition == 'Headache':
        print("Recover, then rest")
    else:
        print("Rest")
else:
    print("Work, work,work")
    

"Перебор последовательности объектов"
for i in [1,2,3]:
    print(i)
    
for ch in "Hi!":
    print(ch)
    
for num in range(5):
    print('Head First Rocks!!!')
  
    
"""
Последние пять строк нужно повторить пять раз с помощью for
В эти пять строк кода нужно добавить отступы, чьобы превратить их в блок кода for
"""

from datetime import datetime

odds = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19,
        21, 23, 25, 27, 29, 31, 33, 35, 37, 39,
        41, 43, 45, 47, 49, 51, 53, 55, 57, 59]

for i in range(5):
    right_this_minute = datetime.today().minute

    if right_this_minute in odds:
        print("This minute seems a little odd.")
    else:
        print("Not an odd minute.")
        

""" 
Python поддерживает два механизма импортирования модулей.
Однако инструкцию import можно использовать двумя способами.

Первый - импортирует именованную функцию в пространтво имен нашей программы, что позволило нам
вызывать функцию по мере необходимости без связывания функции с импортированным модулем.
from datetime import datetime
Второй - это просто импортирование модуля целиком:
import time
"""

import time #Импортировать модуль time
time.sleep(1) #Вызвать метод sleep() из модуля time, чтобы программа ждала 5 секунд перед повторением цикла

