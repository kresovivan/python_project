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
