class Monster:
    #Инициализация аттрибутов
    def __init__(self, name, character):
        self.Name = name
        self.Character = character
    #Метод
    def show(self):
        print("Имя: " + self.Name)
        print("Особенность: " + self.Character)


class GMonster(Monster):
    pass

class SMonster(Monster):
    pass
#Основная программа
Frank = Monster("Фрэнки","Необычный")
Frank.show()
Albert = GMonster("Альберт","Задумчивый")
Albert.show()
Sigmund = SMonster("Зигмунд","Веселый")
Sigmund.show()



