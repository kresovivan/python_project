import random

def initGame():
    global Attemp, Input
    Secret = 'Я задумал число от 1 до 1000'
    print(Secret)
    Attemp = 0
    Input = 0

def playGame():
    global Attemp, Input
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

def endGame():
    global Attemp
    print('Ты пробовал ' + str(Attemp) + ' раз.')

#Осонвная программа
initGame()
playGame()
endGame()