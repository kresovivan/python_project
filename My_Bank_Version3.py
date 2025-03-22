#Версия 3, с использованием словаря счетов

#Берем весь код из файла класса Account

from Account import *

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

accountDict[joesAccountNumber].show()
accountDict[marysAccountNumber].show()
print()

#вызываем разные методы для разных счетов
print('Calling methods of the two accounts...')
accountDict[joesAccountNumber].deposit(50, 'JoePassword')
accountDict[marysAccountNumber].withdraw(345,'MarysPassword')

