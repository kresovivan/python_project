import random

def initGame(Attemp, Input):
    Secret = 'Я задумал число от 1 до 1000'
    print(Secret)

def playGame(Attemp,Input):
    Case = random.randint(1,1000)
    while Input != Case:
        print('Угадай число: ', end='')
        Input = int(input())
        Attemp = Attemp + 1
        if Input < Case:
            print('Слишком маленькое!')
        if Input > Case:
            print('Слишком большое!')
        if Input == Case:
            print("Вы угадали число!")
    return Attemp

def endGame(Attemp):
    print('Ты пробовал ' + str(Attemp) + ' раз.')

#Осонвная программа
initGame(0,0)
Game = playGame(0,0)
endGame(Game)