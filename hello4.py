#Приветствие с кнопками
from tkinter import *

from hello3 import Display

#Константы текста
Answer = ["Супер", "Хорошо", "Так себе", "Плохо", "Ужасно", \
          "Не скажу"]
Diagnose = ["Это здорово!", "Это радует!", "Все возможно", "Это огорчает!" \
            "Это плохо", "Раз ты так думаешь..."]

#Функция события
def buttonClick(Nr):
    Display.config(text=Diagnose[Nr])

#Основная программа
Windows
