prompt = "\nTell me something, and I will repeat it back to you:"
prompt += "\nEnter 'q' to end the program. "
message = ""
active = True
while active:
    message = input(prompt)
    if message == 'q':
        active = False
    else:
        print(message)