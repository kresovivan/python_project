#Приветствие с кнопками
#Окно с событиями
from tkinter import *

#Функция для события
def button1Click():
    Display.config(text="Это радует!")
def button2Click():
    Display.config(text="Это огорчает!")

#Основная программа
Window = Tk()
Display = Label(Window, text = "Привет, как дела?")
Display.pack()
Button1 = Button(Window, text="Хорошо", command=button1Click)
Button2 = Button(Window, text="Плохо",  command=button2Click)
Button1.pack()
Button2.pack()
Window.mainloop()