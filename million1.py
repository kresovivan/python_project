print("Какую сумму ты хочешь инвестировать: ")
Capital = float(input())
print("Процентная ставка: ")
Percent = float(input())
print("На какой срок ты вкладываешь деньги: ")
Term=int(input())
for Value in range(Term):
    Fee = Capital * Percent / 100
    Capital = Capital + Fee
print("Так ты получишь " + str(Capital) + " рублей")
if Capital < 1000000:
    print("Но ты так не станешь миллионером")
else:
    print("Добро пожаловать в Клуб миллионеров!")