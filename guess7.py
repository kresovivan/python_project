import random

def initGame():
    Secret = "Я задумал число от 1 до 1000"
    print(Secret)

def playGame(Attempt, Input):
    Case = random.randint(1,1000)
    # print(Case)
    while Input != Case:
        print("Угадай число: ", end="")
        Input = int(input())
        Attempt += 1
        if Input < Case:
            print("Слишком маленькое число")
        if Input > Case:
            print("Слишком большое число")
        if Input == Case:
            print("Ты угадал число!!!")
    return Attempt

def endGame(Attempt):
    print("Ты пробовал " + str(Attempt) + " раз.")

#Основная программа
initGame()
Game = playGame(0,0)
endGame(Game)