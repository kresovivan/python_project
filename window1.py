#Окно с событиями
from tkinter import *
from tkinter import messagebox

#Функция для события
def button1Click():
    messagebox.showinfo('Ответ', 'Это радует!')
def button2Click():
    messagebox.showinfo('Ответ','Это огорчает!')

#Основная программа
Window = Tk()
Window.title('Привет!')
Window.config(width=260, height=120)
Display = Label(Window, font='Arial 12', text='Как дела?')
Display.place(x=50, y=20, width=160, height=30)  # Добавьте эту строку, чтобы метка отобразилась в окне
Button1 = Button(Window, text='Хорошо', command=button1Click)
Button2 = Button(Window, text ='Плохо', command=button2Click)
Button1.place(x=20, y=70, width=100, height=30)
Button2.place(x=140, y=70, width=100, height=30)
Window.mainloop()  # Запуск основного цикла обработки событий