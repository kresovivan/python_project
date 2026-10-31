import time, sys
ident = 0 # количество пробелов для отступа
identIncreasing = True #Увеличение или уменьшение отступа

try:
    while True:
        print(" " * ident, end="")
        print("********")
        time.sleep(0.1)
        
        if identIncreasing:
            ident = ident + 1
            if ident == 20:
                identIncreasing = False
        else:
            ident = ident - 1
            if ident == 0:
                identIncreasing = True
except KeyboardInterrupt:
    sys.exit()