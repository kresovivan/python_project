num = input("Введите целое число: ")


def square(num):
    if not num.isdigit():
        return "Ошибка ввода"
    num = int(num)
    return num * num


print(num, "Возведение в квадрат: ", square(num))
