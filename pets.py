def describe_pet(pet_name, animal_type='cat'):
    """Выводит информацию о животном"""
    print(f"\nI have a {animal_type}.")
    print(f"My {animal_type}'s name is {pet_name.title()}.")

describe_pet('cat', 'kisunchik')
describe_pet('hamster', 'harry')
describe_pet('dog', 'sharik')


describe_pet(pet_name='kisunchik')