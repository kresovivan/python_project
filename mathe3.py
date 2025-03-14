try:
    while True:
        print('введи число: ')
        Number1 = float(input())
        print('Введи еще одно число: ')
        Number2 = float(input())
        print('А теперь выбери операцию (+,-,*,/): ')
        Operator = input()
        print('Результат = ')
        if Operator == '+':
            print(Number1 + Number2)
        if Operator == '-':
            print(Number1 - Number2)
        if Operator == '*':
            print(Number1 * Number2)
        if Operator == '/':
            if Number2 !=0:
                print(Number1 / Number2)
            else:
                print('Невозможно вычислить')
except:
    print('Не число!')