def describe_pet(animal_type, pet_name):
    """Выводит информацию о животном"""
    print(f"\nI have a {animal_type}.")
    print(f"My {animal_type}'s name is {pet_name.title()}.")

describe_pet('cat', 'kisunchik')
describe_pet('hamster', 'harry')
describe_pet('dog', 'sharik')


describe_pet(animal_type= 'cat', pet_name='kisunchik')