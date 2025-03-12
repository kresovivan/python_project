def function():
    print('second')


def print_sum(c, b):
    print(f"Сумма {c} и {b} равна {c + b}")
print_sum(10, 15)  # Выведет: Сумма 10 и 15 равна 25

def shout(text):
    return text.upper()

yell = shout

def greet(func):
    greeting = func("Hello")  # вызываем функцию
    print(greeting)

def get_user():
    name = "Иван"
    age = 25
    return name, age

user_name, user_age = get_user()
print(user_name, user_age)  # Выведет Иван 25