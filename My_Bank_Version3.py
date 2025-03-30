#Версия 3, с использованием словаря счетов

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

accountDict[joesAccountNumber].show()
accountDict[marysAccountNumber].show()
print()

#вызываем разные методы для разных счетов
print('Calling methods of the two accounts...')
accountDict[joesAccountNumber].deposit(50, 'JoePassword')
accountDict[marysAccountNumber].withdraw(345,'MarysPassword')
accountDict[marysAccountNumber].deposit(100, 'MarysPassword')

#Отображаем счета
accountDict[joesAccountNumber].show()
accountDict[marysAccountNumber].show()

#Создаем новый счет с информацией от пользователя
print()
userName = input('What is the name for the new user account? ')
userBalance = input('What is the starting balance for this account? ')
userBalance = int(userBalance)
userPassword = input('Wrat is the password you want to use for this account? ')

oAccount = Account(userName, userBalance, userBalance)
newAccountNumber = nextAccountNumber
accountDict[newAccountNumber] = oAccount
print('Account number for new account is:', newAccountNumber)
nextAccountNumber = nextAccountNumber + 1

#Отображаем вновь созданный счет пользователя
accountDict[newAccountNumber].show()

#Вносим 100 на новый счет
accountDict[newAccountNumber].deposit(100, userPassword)
userBalance = accountDict[newAccountNumber].getBalance(userBalance)
print()
print('After depositing 100, the users balance is: ', userBalance)

# отображаем новый счет
accountDict[newAccountNumber].show()