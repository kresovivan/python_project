#Окно с событиями
from tkinter import *

#Функция для события
def button1Click():
    Display.config(text='Это радует!')
def button2Click():
    Display.config(text='Это огорчает!')

#Основная программа
Window = Tk()
Display = Label(Window, font='Arial 16', text='Привет!')
Display.pack()  # Добавьте эту строку, чтобы метка отобразилась в окне
Button1 = Button(Window, text='Хорошо', command=button1Click)
Button2 = Button(Window, text ='Плохо', command=button2Click)
Button1.pack()
Button2.pack()
Window.mainloop()  # Запуск основного цикла обработки событий