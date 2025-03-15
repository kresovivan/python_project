class Monster:
    #Инициализация аттрибута
    def __init__(self, name, character):
        self.__Name = name
        self.__Character = character
        #Метод c одним подчеркиванием защищенный, если с двумя подчеркиваниями, то метод приватный
    def _Type(self):
        return "Монстр"
    def show(self):
        print('Имя: ' + self.__Name)
        print('Особенность: ' + self.__Character)
        print('Тип: ' + self._Type())

class GMonster(Monster):
    def _Type(self):
        return 'Сын монстра'

class SMonster(Monster):
    def _Type(self):
        return 'Сын монстра'

