import random


# Функция для создания пустого поля
def create_board():
    return [["O" for _ in range(10)] for _ in range(10)]


# Функция для вывода поля на экран
def print_board(board):
    print("  " + " ".join(str(i) for i in range(10)))
    for i, row in enumerate(board):
        print(i, " ".join(row))


# Функция для размещения корабля на поле
def place_ship(board):
    ship_row = random.randint(0, 9)
    ship_col = random.randint(0, 9)
    board[ship_row][ship_col] = "S"
    return (ship_row, ship_col)


# Функция для проверки попадания
def check_hit(board, row, col):
    if board[row][col] == "S":
        board[row][col] = "X"
        return True
    elif board[row][col] == "O":
        board[row][col] = "~"
        return False
    else:
        return None


# Основная функция игры
def play_battleship():
    print("Добро пожаловать в игру 'Морской бой'!")
    print("Ваша цель — потопить корабль противника.")

    # Создаем поля для игрока и компьютера
    player_board = create_board()
    computer_board = create_board()

    # Размещаем корабли
    player_ship = place_ship(player_board)
    computer_ship = place_ship(computer_board)

    # Основной игровой цикл
    while True:
        print("\nВаше поле:")
        print_board(player_board)

        # Ход игрока
        try:
            print("\nВаш ход!")
            guess_row = int(input("Введите номер строки (0-9): "))
            guess_col = int(input("Введите номер столбца (0-9): "))

            if guess_row < 0 or guess_row > 9 or guess_col < 0 or guess_col > 9:
                print("Ошибка! Введите числа от 0 до 9.")
                continue

            result = check_hit(computer_board, guess_row, guess_col)
            if result is None:
                print("Вы уже стреляли в эту клетку!")
            elif result:
                print("Поздравляю! Вы потопили корабль противника!")
                break
            else:
                print("Мимо! Вы промахнулись.")
        except ValueError:
            print("Ошибка! Введите числа от 0 до 9.")
            continue

        # Ход компьютера
        print("\nХод компьютера...")
        comp_row = random.randint(0, 9)
        comp_col = random.randint(0, 9)

        result = check_hit(player_board, comp_row, comp_col)
        if result is None:
            continue
        elif result:
            print("Компьютер потопил ваш корабль! Вы проиграли.")
            break
        else:
            print("Компьютер промахнулся.")


# Запуск игры
play_battleship()