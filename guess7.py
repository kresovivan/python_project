import random

def initGame():
    global Attempt, Input
    Secret = "Я задумал число от 1 до 1000"
    print(Secret)
    Attempt=0
    Input=0

def playGame():
    global Attempt, Input
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

def endGame():
    global  Attempt
    print("Ты провобовал " + str(Attempt) + " раз.")

#Основная программа
initGame()
playGame()
endGame()