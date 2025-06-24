print("Напиши короткий текст (небольшой без пробелов) : ")
Text1 = input()
Text2 = ""
Chain = len(Text1)
for Nr in range(0, Chain):
    Text2 += Text1[Chain-Nr-1]
print(Text2)
if Text1 == Text2:
    print("Палиндром")