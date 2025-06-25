# Модуль с монстрами
class Monster :
  # Инициализация атрибута
  def __init__(self, name, character) :
    self.__Name = name
    self.__Character = character
  # Метод
  def _Type(self) :
    return "Монстр"
  def show(self) :
    print("Имя: " + self.__Name)
    print("Особенность: " + self.__Character)
    print("Тип:   " + self._Type())

class GMonster (Monster):
  # Метод
  def _Type(self) :
    return "Дух монстра"

class SMonster (Monster):
  # Метод
  def _Type(self) :
    return "Душа монстра"
