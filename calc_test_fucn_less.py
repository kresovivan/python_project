"""
Что нужно сделать:
Создай простые математические функции.
Напиши 4 маленькие функции, каждая из которых принимает два числа (a и b) и возвращает результат:

summa(a, b) — возвращает сложение (a + b).
diff(a, b) — возвращает вычитание (a - b).
mult(a, b) — возвращает умножение (a * b).
div(a, b) — возвращает деление (a / b).

Создай функцию высшего порядка.
Напиши функцию calculate(operation, x, y).

Параметр operation будет принимать другую функцию (одну из тех, что ты написал выше).
Параметры x и y — это числа, с которыми нужно работать.
Внутри этой функции просто вызови переданную функцию operation с аргументами x и y и верни результат.
Проверь работу.
Вызови функцию calculate четыре раза, передавая в неё разные функции-операции и любые числа на твой выбор. 
Выведи результаты на экран.
"""

def summa(a,b):
    return a + b

def diff(a,b):
    return a - b

def mult(a,b):
    return a * b

def div(a,b):
    return a / b

def calculate(operation, x, y):
    return operation(x, y)

def smart_calculate(operation, x, y):
    
    operation_name = operation.__name__
    print(f"\n--- Запуск операции '{operation_name}' над числами {x} и {y} ---")
    
    # 1. Проверка (дополнительная логика)
    # Мы проверяем, являются ли аргументы числами
    if not (isinstance(x, (int, float)) and isinstance(y, (int, float))):
        print("Ошибка: Введены не числа!")
        return None
    
    result = calculate(operation, x, y)
    
    print(f"Результат вычисления: {result}")
    return result

print(smart_calculate(summa, 2, 3))
print(smart_calculate(mult, 2, 3))
print(smart_calculate(diff, 5, 2))
print(smart_calculate(div, 5, 2))


