# Приветствие со списком
from tkinter import *

# Константы текста
Answer = ["Супер", "Хорошо", "Так себе", "Плохо", "Ужасно", "Не скажу"]
Diagnose = ["Это здорово!", "Это радует!", "Все возможно.", \
            "Это огорчает!", "Это плохо!", "Раз ты так думаешь ..."]

# Функция события
def listboxSelect(event) :
  Select = Box.curselection()
  Nr = Select[0]
  Display.config(text=Diagnose[Nr])

# Основная программа
Window = Tk()
Window.title("Привет!")
Window.config(width=260, height=230)
Display = Label(Window, text="Как это сделать?")
Display.place(x=20, y=10, width=160, height=30)

# Список
Box = Listbox(Window)
for Nr in range(0,6) :
  Box.insert(Nr, Answer[Nr])
Box.bind("<<ListboxSelect>>", listboxSelect)
Box.place(x=30,y=50, width=200, height=150)

# Цикл событий
Window.mainloop()