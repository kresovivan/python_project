from main1 import *
"""
def test_sum_list() -> None:
— Объявляет тестовую функцию. Название начинается с test_, чтобы pytest её нашёл.
data = [2, 3, 4]
— Подготавливает входные данные: список чисел.
assert sum_list(data) == 10
— Проверяет, что функция sum_list возвращает правильную сумму (2+3+4 = 9, а не 10).
"""
def test_sum_list()->None:
    data = [2,3,4]
    assert sum_list(data) == 10

""""
test_main1.py::test_sum_list FAILED    
    def test_sum_list()->None:
        data = [2,3,4]
>       assert sum_list(data) == 9                                                                                                                                                  
E       assert 10 == 9
E        +  where 10 = sum_list([2, 3, 4])
"""

def test_pow_n() -> None:
    my_pow = pow_n(0)
    for it in range(1,9):
        assert my_pow(it) == 1

    my_pow = pow_n(3)
    assert my_pow(2) == 8

