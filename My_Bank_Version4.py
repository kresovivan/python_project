#Берем весь код из файла класса Account

from Account import *
from My_Bank_Version2 import userName, userPassword

#наичинаем с пустого списка счетов
accountDict = { }
nextAccountNumber = 0


#Создаем два счета
oAccount = Account('Joe', 100, 'JoesPassword')
joesAccountNumber = nextAccountNumber
accountDict[joesAccountNumber] = oAccount
print('Joe account number is: ', joesAccountNumber)
nextAccountNumber = nextAccountNumber + 1

oAccount = Account('Mary', 100, 'MarysPassword')
marysAccountNumber = nextAccountNumber
accountDict[marysAccountNumber] = oAccount
print('Mary account number is: ', marysAccountNumber)
nextAccountNumber = nextAccountNumber + 1

while True:
    print()
    print('Press b to get the balance')
    print('Press d to make deposit')
    print('Press o to open a new account')
    print('Press w to make a withdrawl')


