#Окно с событиями
from tkinter import *

class Dialog():
    def __init__(self, Title, Text, But1, But2):
        self.Window = Tk()
        self.Window.title(Title)
        self.Window.config(width=260, height=120)
        self.Display = Label(self.Window, font='Arial 12', text=Text)
        self.Display.place(x=50, y=20, width=160, height=30)  # Добавьте эту строку, чтобы метка отобразилась в окне
        self.Button1 = Button(self.Window, text=But1, command=self.button1Click)
        self.Button2 = Button(self.Window, text =But2, command=self.button2Click)
        self.Button1.place(x=20, y=70, width=100, height=30)
        self.Button2.place(x=140, y=70, width=100, height=30)
        self.Window.mainloop()  # Запуск основного цикла обработки событий


#Методы для события
    def button1Click(self):
        self.Display.config(text='Это радует!')
    def button2Click(self):
        self.Display.config(text='Это огорчает!')

#Основная программа
Window = Dialog('Привет', 'Как дела', 'Хорошо', 'Плохо')