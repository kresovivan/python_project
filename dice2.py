import random, time

print('Давай бросим кубики!')
Attemp = 0
YourNumber = 0
MyNumber = 0

#Игральные кубики
for RowNumber in range(5):
    print(str(RowNumber + 1) + '. Раунд')
    print('Твой бросок: ', end='')
    Shoot1 = random.randint(1,6) #Твой бросок
    time.sleep(2) #Ожидание 2 секунды
    print(Shoot1)
    print('Мой бросок: ', end='')
    Shoot2 = random.randint(1,6) #Мой бросок
    time.sleep(2)
    print(Shoot2)
    if Shoot1 > Shoot2:
        YourNumber = YourNumber + 1
    if Shoot1 < Shoot2:
        MyNumber = MyNumber + 1
    print(str(YourNumber) + ' и ' + str(MyNumber))
    time.sleep(3)
    print()
#Вычисления
if YourNumber > MyNumber:
    print('Ты выиграл!')
elif YourNumber < MyNumber:
    print('Я выиграл!!!')
else:
    print('Ничья')