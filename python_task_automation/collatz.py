def collatz_safe():
    while True:
        try:
            n = int(input("Введите натуральное число: "))
            if n < 1:
                print("Число должно быть больше 0.")
                continue
            break
        except ValueError:
            print("Это не число. Попробуйте снова.")
    print(n, end="")
    
    while n != 1:
        n = n // 2 if n % 2 == 0 else n * 3 + 1
        print(" →", n, end="")
    print()


collatz_safe()