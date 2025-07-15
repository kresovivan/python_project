def print_models(unprinted_designs, completed_models):
    while unprinted_designs:
        current_design = unprinted_designs.pop()
        print(f"printing model: {current_design}")
        completed_models.append(current_design)
"""Цикл последовательно печатает каждую модель до конца списка. 
После печати каждая модель перемещается в список completed_models."""


def show_completed_models(completed_models):
    print("\nThe following models have been printed")
    for completed_model in completed_models:
        print(completed_model)
"""Выводит информацию обо всех напечатанных моделях"""

unprinted_designs = ["phone_case","robot","shoes"]
completed_models = []

print_models(unprinted_designs, completed_models)
show_completed_models(completed_models)


