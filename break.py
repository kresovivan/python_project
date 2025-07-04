correct_password = "12345"

while True:
    password = input("Введите пароль: ")
    if password == correct_password:
        print("Доступ разрешён!")
        break  # выход, если пароль верный
    print("Неверный пароль, попробуйте ещё раз.")