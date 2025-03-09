import random
from multiprocessing.pool import rebuild_exc

SUIT_TUPLE = ('Spades', 'Hearts', 'Clubs', 'Diamonds')
RANK_TUPLE = ('Ace', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King')

NCARDS = 8


# Проходим по колоде и эта функция возвращает случайную карту из колоды

def getCard(deckListIn):
    thisCard = deckListIn.pop()  # Снимаем одну карту с верхней части колоды и возвращаем
    return thisCard


# Проходим по колоде и эта функция возвращает перемешанную копию kolоды

def shuffle(deckListIn):
    deckListOut = deckListIn.copy()  # создаем копию стартовой колоды
    random.shuffle(deckListOut)
    return deckListOut


# Основной код

print('Welcome to Higher or Lower!!!')
print('You have to choose whether the next card to be shown will be higher or lower than the current card.')
print('Getting it right adds 20 points; get it wrong and you lose 15 points')
print('You have 50 points to start.')
print()

startingDeckList = []
for suit in SUIT_TUPLE:
    for thisValue, rank in enumerate(RANK_TUPLE):
        cardDict = {'rank': rank, 'suit': suit, 'value': thisValue + 1}
        startingDeckList.append(cardDict)

score = 50

while True:  # Несколько игр
    print()
    gameDeckList = shuffle(startingDeckList)
    currentCardDict = getCard(gameDeckList)
    currentCardRank = currentCardDict['rank']
    currentCardValue = currentCardDict['value']
    currentCardSuit = currentCardDict['suit']
    print('Starting card is:', currentCardRank + ' of ' + currentCardSuit)
    print()

    for cardNumber in range(0, NCARDS):  # Играем в одну игру из этого количества карт#
        answer = input('Will the next card be higher or lower than the ' +
                       currentCardRank + ' of ' +
                       currentCardSuit + '? (enter h or 1): ')
    answer = answer.casefold()
    nextCardDict = getCard(gameDeckList)
    nextCardRank = nextCardDict['rank']
    nextCardSuit = nextCardDict['suit']
    nextCardValue = nextCardDict['value']
    print('Next card is:', nextCardRank + ' of ' + nextCardSuit)

    if answer == 'h':
        if nextCardValue > currentCardValue:
            print('You got it right, it was higher')
            score += 20
        else:
            print('Sorry, it was not higher')
            score -= 15

    elif answer == 'l':
        if nextCardValue < currentCardValue:
            score += 20
            print('You got it right, it was lower')
        else:
            print('Sorry, it was not lower')
            score -= 15
            print('Your score is:', score)
            print()
            currentCardRank = nextCardDict['rank']
            currentCardValue = nextCardDict['value']

            goAgain = input('To play again, press enter, or "q" to quit: ')
            if goAgain == 'q':
                break
