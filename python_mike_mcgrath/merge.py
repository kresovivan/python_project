"""
Сортровка слииянием, используестя
при сортивроке больших массивов данных
"""


def merge_sort(array):
    if len(array) <= 1:
        return
    mid = len(array) // 2
    left, right = array[:mid], array[mid:]

    merge_sort(left)
    merge_sort(right)

    i = j = k = 0
    while i < len(left) and j < len(right):
        if left[i] < right[j]:
            array[k] = left[i]
            i += 1
        else:
            array[k] = right[j]
            j += 1
        k += 1
    array[k:] = left[i:] + right[j:]  # ← хвост одним махом


array = [5, 3, 1, 2, 6, 4]
merge_sort(array)
print("Массив", array)  # [1, 2, 3, 4, 5, 6]
