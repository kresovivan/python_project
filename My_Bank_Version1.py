#Версия 1, использующая явные переменные для каждого объекта Account

#Берем весь код из файла класса Account

from Account import *

#создаем два счета

oJoesAccount = Account('Joe', 100, 'JoesPassword')
print('Created an account for Joe')
oMarrysAccount = Account('Marry', 1000,'MarrysPassword')
print('Created an account for Marry')
oJoesAccount.show()
oMarrysAccount.show()
print()

#вызваем разные методы для разных счетов
print('Calling methods of the two accounts ...')
oJoesAccount.deposit(50, 'JoesPassword')
oMarrysAccount.withdraw(345, 'MarrysPassword')
oMarrysAccount.deposit(100, 'MarrysPassword')

#Отображаем счета
oJoesAccount.show()
oMarrysAccount.show()

#Создаем новый счет с информацией о пользователе
print()
UserName = input('Whats is the name for the new user account? ')
UserBalance = input('What is the starting balance for this account? ')
UserBalance = int(UserBalance)
UserPassword = input('What is the password you want to use for this account? ')
oNewAccount = Account(UserName, UserBalance, UserPassword)

#отображаем внось созданный счет пользователя
oNewAccount.show()
#вносим 100 на новый счет
oNewAccount.deposit(100, UserPassword)
usersBalance = oNewAccount.getBalance(UserPassword)
print()
print('After depositing 100, the users balanse is:', usersBalance)

#Отображаем новый счет
oNewAccount.show()