import random

Ball = []
#Все шары еще не вытащены
for Nr in range(1,50):
    Ball.append(0)
Case = random.randint(1,49)
#Вытягивается 6 шаров
for Nr in range(6):
    #Поиск неиспользованных шаров
    while Ball[Case] == 1:
        Case = random.randint(1,49)
        #Пометка использованного шара вытащенным
    Ball[Case] = 1
    print("№ " + str(Nr+1) + " => " + str(Case))