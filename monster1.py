class Monster:
    #Аттрибут
    Name = "Фрэнки"
    Character = "Необычный"
    #Метод
    def show(self):
        print("Имя: " + self.Name)
        print("Особенность: " + self.Character)

#Основная программа
Frank = Monster()
Frank.show()

