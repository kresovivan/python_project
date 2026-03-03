"""
| Итерация | `letter` | Первая проверка `in vowels` | Вторая проверка `not in found` | Действие            | `found` после |
| -------- | -------- | --------------------------- | ------------------------------ | ------------------- | ------------- |
| 1        | `'M'`    | False                       | —                              | пропуск             | `[]`          |
| 2        | `'i'`    | **True**                    | `'i' not in []` → **True**     | **добавляем**       | `['i']`       |
| 3        | `'l'`    | False                       | —                              | пропуск             | `['i']`       |
| 4        | `'l'`    | False                       | —                              | пропуск             | `['i']`       |
| 5        | `'i'`    | **True**                    | `'i' not in ['i']` → **False** | пропуск (уже есть!) | `['i']`       |
| 6        | `'w'`    | False                       | —                              | пропуск             | `['i']`       |
| 7        | `'a'`    | **True**                    | `'a' not in ['i']` → **True**  | **добавляем**       | `['i', 'a']`  |
| 8        | `'y'`    | False                       | —                              | пропуск             | `['i', 'a']`  |
| 9        | `'s'`    | False                       | —                              | пропуск             | `['i', 'a']`  |
"""

vowels = ["a", "e", "i", "o", "u"]
# слово для проверки
word = input("Введите слово для поиска гласных букв: ")
found = []

for letter in word:
    if letter in vowels:
        if letter not in found:
            found.append(letter)
for vowel in found:
    print(vowel)

"""
found.append(letter)
# │      │       │
# │      │       └── что добавляем (букву 'i', 'a' и т.д.)
# │      └── метод "добавить в конец"
# └── список, в который добавляем
"""


def digit_sum(n):
    """Вычисляет сумму цифр числа (упрощенно)"""
    return sum(int(d) for d in str(abs(n)))


def sort_by_digit_sum(arr):
    """Сортирует по сумме цифр"""
    return sorted(arr, key=digit_sum)


# Использование
numbers = [56, 12, 33, 101, 7, 24, 111, 10]
result = sort_by_digit_sum(numbers)
print(f"Исходные: {numbers}")
print(f"Результат: {result}")


def maximize_number(A, B):
    a = list(A)
    b = sorted(B, reverse=True)  # сортируем цифры B по убыванию

    for i in range(len(a)):
        if b and a[i] < b[0]:  # если есть цифры в B и они больше текущей
            a[i] = b.pop(0)  # заменяем и удаляем использованную цифру

    return "".join(a)


# Проверка
print(maximize_number("123", "456"))  # 653
print(maximize_number("5271", "934"))  # 9571
print(maximize_number("1111", "999"))  # 9911
