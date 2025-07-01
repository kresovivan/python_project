available_toppings = ["mushrooms", "olives", "green peppers", "pepproni",
                      "pineaple", "extra cheese"]

requested_toppings = ["mushrooms", "french fries", "chipps", "extra cheese"]

for requested_topping in requested_toppings:
    if requested_topping in available_toppings:
        print(f"Adding {requested_topping}")
    else:
        print(f"Sorry we don't have {requested_topping}.")