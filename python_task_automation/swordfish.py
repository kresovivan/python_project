while True:
    print("Who are you?")
    name = input()
    if name !="Joe":
        continue
    print("Hello, Joe. What is the password? (It is a fish)")
    password = input()
    if password=="swordfish":
        break
print('Access granted.')


"""
        ┌─────────────────────┐
        │  while True:        │
        └──────────┬──────────┘
                   ↓
        ┌─────────────────────┐
        │  print("Who are...")│
        └──────────┬──────────┘
                   ↓
        ┌─────────────────────┐
        │  name = input()     │
        └──────────┬──────────┘
                   ↓
          name != "Joe"?
          ┌───────┴───────┐
         Да              Нет
          ↓               ↓
     continue      print("Hello, Joe...")
     (к началу)           ↓
                   password = input()
                          ↓
                password == "swordfish"?
                  ┌───────┴───────┐
                 Нет             Да
                  ↓               ↓
             (к началу)        break
                                  ↓
                          print("Access granted.")

"""

