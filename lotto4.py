import random


#Функция
def exchange(x1,x2):
    Swap = x1
    x1 = x2
    x2 = Swap
    return x1, x2

def bublesort(x, Index):
    for i in range(Index):
        for j in range(Index-i-1):
            if x[j] > x[j+1]:
                x[j], x[j+1] = exchange(x[j], x[j+1]);

#Основная программа
Ball = []
Lotto = [0,0,0,0,0,0]
# Все шары еще не "Вытащены"
for Nr in range(1,50):
    Ball.append(False)
Case = random.randint(1,49)

#Вытягивается шесть шаров
for Nr in range(6):
    while Ball[Case]:
        Case.random.randint(1,49)
#Пометка использованного шара вытащенным
Ball[Case] = True
Lotto[Nr] = Case

#Cортировка и отображение
bublesort(Lotto, 6)
print(Lotto)
