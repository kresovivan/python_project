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

print('Welcome to Higher or Lower!!!')
print('You have to choose whether the next card to be shown will be higher or lower than the current card.')
print('Getting it right adds 20 points; get it wrong and you lose 15 points')
print('You have 50 points to start.')
print()

startingDeckList = []
for suit in SUIT_TUPLE:
    for thisValue, rank in enumerate(RANK_TUPLE):
        cardDict = {'rank':rank, 'suit':suit, 'value':thisValue + 1}
        startingDeckList.append(cardDict)