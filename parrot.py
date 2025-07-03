prompt = "\nTell me something, and I will repeat it back to you:"
prompt += "\nEnter 'q' to end the program. "
message = ""
while message != 'q':
    message = input(prompt)
    print(message)
if message != 'q':
   print(message)