import random

Secret = 'Я задумал число от 1 до 1000'
Case = random.randint(1, 1000)
print(Secret)
Attemp = 0
Input = 0
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
    if Input == 0:
        print('Правильно число было: ' + str(Case))
        break
print('Ты пробовал ' + str(Attemp) + ' раз.')