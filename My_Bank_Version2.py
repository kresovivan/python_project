#Версия 2, c использованием списка счетов

#Берем весь код из файла класса Account

from Account import *
from My_Bank_Version1 import oNewAccount

#наичинаем с пустого списка счетов
accountList = [ ]

#Создаем два счета
oAccount = Account('Joe', 100, 'JoesPassword')
accountList.append(oAccount)
print('Joe account number is 0')

oAccount = Account('Mary', 100, 'MarysPassword')
accountList.append(oAccount)
print('Mary account number is 1')

accountList[0].show()
accountList[1].show()
print()

#Вызываем разные методы для разных счетов
print('Calling methods the two accounts...')
accountList[0].deposit(50, 'JoesPassword')
accountList[1].withdraw(345, 'MarysPassword')
accountList[1].deposit(1000, 'MarysPassword')

#Отображаем счета
accountList[0].show()
accountList[1].show()

#Создаем новый счет с информацией от пользователя
print()
userName = input('What is the name for the new user account? ')
userBalance = input('What is the starting balance for this account? ')
userBalance = int(userBalance)
userPassword = input('What is the password you want to use for this account? ')

oAccount = Account(userName, userBalance, userPassword)
accountList.append(oAccount) #добавляем к списку счетов

#отображаем вновь созданный счет пользователя
print('Created new account, account number is 2')
accountList[2].show()

#Вносим 100 на новый счет
accountList[2].deposit(100, userPassword)
userBalance = accountList[2].getBalance(userPassword)
print()
print('After depositing 100, the user balance is:', userBalance)

# отображаем новый счет
accountList[2].show()



