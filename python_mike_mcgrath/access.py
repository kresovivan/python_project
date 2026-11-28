file = open("example.txt", "w")
print("Имя файла", file.name)
print("Режим открытия файла: ", file.mode)
print("Чтение файла: ", file.readable())
print("Запись файла: ", file.writable())


def get_status(f):
    if not f.closed:
        return "Открыт"
    else:
        return "Закрыт"


print("\nСтатус файла: ", get_status(file))
file.close()
print("\nСтатус файла: ", get_status(file))
