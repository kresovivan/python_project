import sys, keyword

print("Версия python: ", sys.version)  # Версия Python
print("Местонахождение интерпретатора: ", sys.executable)  # Где расположен итерпретатор
print("Путь поиска модулей: ")
for folder in sys.path:
    print(folder)

print("Ключевые слова Python: ")
for word in keyword.kwlist:
    print(word)
