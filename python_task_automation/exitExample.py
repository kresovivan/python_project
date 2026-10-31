import sys

while True:
    print("Введите exit для выхода") 
    response = input()
    if response == "exit":
        sys.exit()
    print("Вы ввели " + response + ".")