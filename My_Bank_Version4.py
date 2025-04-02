#Берем весь код из файла класса Account

from Account import *
from My_Bank_Version2 import userName, userPassword
from My_Bank_Version3 import accountDict

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
    print('Press w to make a withdrawal')
    print('Press s to show all accounts')
    print('Press q to quit')
    print()

    action = input('What do you want to do? ')
    action = action.lower()
    action = action[0]
    print()

    if action == 'b':
        print('*** Get Balance ***')
        userAccountNumber = input('Please enter your account number: ')
        userAccountNumber = int(userAccountNumber)
        userAccountPassword = input('Please enter the password: ')
        oAccount = accountDict[userAccountNumber]
        theBalance = oAccount.getBalance(userAccountPassword)
        if theBalance is not None:
            print('Your balance is: ', theBalance)

    elif action == 'd':
        print('*** Deposit ***')
        userAccountNumber = input('Please enter your account number: ')
        userAccountNumber = int(userAccountNumber)
        userDepositAmount = input('Please enter amount to deposit: ')
        userDepositAmount = int(userDepositAmount)
        userPassword = input('Please enter the password: ')
        oAccount = accountDict[userAccountNumber]
        theBalance = oAccount.deposit(userDepositAmount, userPassword)
        if theBalance is not None:
            print('Your balance is: ', theBalance)

    elif action == 'o':
        print ('*** Open Account***')
        userName = input('What is the name for the new user account? ')
        userStartingAmount = input('What is the starting balance for this account? ')
        userStartingAmount = int(userStartingAmount)
        userPassword = input('What is the password you want to use for this account? ')
        oAccount = Account(userName, userStartingAmount, userPassword)
        accountDict[nextAccountNumber] = oAccount
        print('Your new account number is:', nextAccountNumber)
        nextAccountNumber = nextAccountNumber + 1
        print()

    elif action == 's':
        print('Show:')
        for userAccountNumber in accountDict:
            oAccount = accountDict[userAccountNumber]
            print(' Account number:', userAccountNumber)
            oAccount.show()

    elif action == 'q':
        break

    elif action =='w':
        print('*** Withdraw ***')
        userAccountNumber = input('Please enter your account number: ')
        userAccountNumber = int(userAccountNumber)
        userWithdrawalAmount = input('Please enter the amount to withdraw: ')
        userWithdrawalAmount = int(userWithdrawalAmount)
        userPassword = input('Please enter the password: ')
        oAccount = accountDict[userAccountNumber]
        theBalance = oAccount.withdraw(userWithdrawalAmount, userPassword)
        if theBalance is not None:
            print('Withdraw:', userWithdrawalAmount)
            print('Your new balance is: ', theBalance)

        else:
            print('Sorry, that was not a valid action. Please try again')

        print('Done')