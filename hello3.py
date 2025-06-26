from tkinter import *

#Фукнция для события
def button1Click():
    Display.config(text="Это здорово")

def button2Click():
    Display.config(text="Это радует!")

def button3Click():
    Display.config(text="Все возможно")

def button4Click():
    Display.config(text="Это огорчает!")

def button5Click():
    Display.config(text="Это плохо!")

def button6Click():
    Display.config(text="Раз ты так думаешь...")

#Основная программа
Window = Tk()
Window.title("Привет!")
Window.config(width=300, height=190)
Display = Label(Window, text="Как это сделать?")
Display.place(x=80, y=10,width=160, height=30)

#Текст на кнопках
Button1 = Button(Window, text="Супер",    command=button1Click)
Button2 = Button(Window, text="Хорошо",   command=button2Click)
Button3 = Button(Window, text="Так себе", command=button3Click)
Button4 = Button(Window, text="Плохо",    command=button4Click)
Button5 = Button(Window, text="Ужасно",   command=button5Click)
Button6 = Button(Window, text="Не скажу", command=button6Click)

#Позиционирование кнопок
Button1.place(x=20,  y=60,   width=120, height=30)
Button2.place(x=160, y=60,   width=120, height=30)
Button3.place(x=20,  y=100,  width=120, height=30)
Button4.place(x=160, y=100,  width=120, height=30)
Button5.place(x=20,  y=140,  width=120, height=30)
Button6.place(x=160, y=140,  width=120, height=30)

#Цикл событий
Window.mainloop()
