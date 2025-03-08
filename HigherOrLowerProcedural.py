import random

SUIT_TUPLE = ('Spades', 'Hearts', 'Clubs', 'Diamonds')
RANK_TUPLE = ('Ace', '2','3','4','5','6','7','8','9','10','Jack','Queen','King')

NCARDS = 8

#Проходим по колоде и эта функция возвращает случайную карту из колоды

def getCard(deckListIn):
    thisCard = deckListIn.pop() #Снимаем одну карту с верхней части колоды и возвращаем
    return thisCard

#Проходим по колоде и эта функция возвращает перемешанную копию колоды
def shuffle(deckListIn):
    deckListOut = deckListIn.copy() # создаем копию стартовой колоды
    random.shuffle(deckListOut)
    return deckListOut

#Основоной код