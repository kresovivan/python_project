# Сортировка выбором (сортировка массива на месте) Медленный на больших массивах (сложность O(n²))
def selection_sort(array):
    # Проходим по каждой позиции массива
    for index in range(0, len(array) - 1):
        value = array[index]
        current = index
        for element in range(index + 1, len(array)):
            if array[element] < array[current]:
                current = element
        array[index] = array[current]
        array[current] = value
        print("\tРассматривает элемент[", index, "] из", array)


array = [5, 3, 1, 2, 6, 4]
print("Сортировка выбором...\nМассив", array)

selection_sort(array)
print("Массив", array)
