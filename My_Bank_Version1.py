#Версия 1, использующая явные переменные для каждого объекта Account

#Берем весь код из файла класса Account

from Account import *

#создаем два счета

oJoesAccount = Account('Joe', 100, 'JoesPassword')
print('Created an account gor Joe')
oMarrysAccount = Account('Marry', 12345,'MarrysPasword')
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
