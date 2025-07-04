responses = {}

#Установка флага продолжения опроса
polling_active = True

while polling_active:
    #Запрос имени и ответа пользователя
    name = input("\nWhat is your name? ")
    response = input("Which mountain would you like to climb someday? ")
    #Ответ сохраняется в словаре
    responses[name] = response
    print(responses)
