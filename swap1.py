def exchange(x1, x2):
    Swap = x1
    x1 = x2
    x2 = Swap
    return x1,x2

#Основная программа
print("Введите число: ", end="")
Number1 = int(input())
print("И еще одно: ", end="")
Number2 = int(input())
print("До обмена: " + str(Number1) + " и " + str(Number2))
Number1, Number2 = exchange(Number1, Number2)
print("После обмена: " + str(Number1) + " и " + str(Number2))