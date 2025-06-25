class Monster:
    #Инициализация аттрибутов
    def __init__(self, name, character):
        self.Name = name
        self.Character = character
    #Метод
    def Type(self):
        return "Монстр"

    def show(self):
        print("Имя: " + self.Name)
        print("Особенность: " + self.Character)
        print("Тип: " + self.Type())


class GMonster(Monster):
    def Type(self):
        return "Дух монстра"

class SMonster(Monster):
    def Type(self):
        return "Душа монстра"
