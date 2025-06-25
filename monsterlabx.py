class Monster:
    #Инициализация аттрибутов
    def __init__(self, name, character):
        self.__Name = name
        self.__Character = character
    #Метод
    def __Type(self):
        return "Монстр"

    def show(self):
        print("Имя: " + self.__Name)
        print("Особенность: " + self.__Character)
        print("Тип: " + self.__Type())


class GMonster(Monster):
    def __Type(self):
        return "Дух монстра"

class SMonster(Monster):
    def __Type(self):
        return "Душа монстра"
