#Основная программа контролирует банк, состоящий из счетов

#Берем весь код класса банка
from Bank import *
from My_Bank_Version3 import joesAccountNumber, marysAccountNumber

# создаем экземпляр банка
oBank = Bank()

#Основной код
#Создаем два тестовых счета
joesAccountNumber = oBank.createAccount('Joe', 100, 'JoesPassword')
print('Joes account number is:', joesAccountNumber)

while True:
    print()
    print('To get an account balance, press b')
    print('To close an account, press c')
    print('To make a deposit, press d')
    print('To open a new account, press o')
    print('To quit, press q')
    print('To show all accounts, press s')
    print('To make a withdrawal, press w')
    print()

    action = input('What do you want to do? ')
    action = action.lower()
    action = action[0] #Берем первую букву
    print()

    if action == 'b':
        oBank.balance()

    elif action == 'c':
        oBank.closeAccount()

    elif action == 'd':
        oBank.deposit()

    elif action == 'o':
        oBank.openAccount()

    elif action == 's':
        oBank.show()

    elif action == 'q':
        break

    elif action == 'w':
        oBank.withdraw()

    else:
        print('Sorry, that was not a valid action. Please try again.')

    print('Done')