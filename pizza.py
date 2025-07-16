#Сохранение инфолрмации о заказнной пицце
def make_pizza(*toppings):
    """Выводит описание пиццы"""
    print("\nMaking a pizza with the following toppings:")
    for topping in toppings:
        print(f" - {topping}")

make_pizza("green peppers", 'extrа cheese')

