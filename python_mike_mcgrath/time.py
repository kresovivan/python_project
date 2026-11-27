from datetime import datetime

today = datetime.today()
print("Сегодня ", today)

for attr in ["year", "month", "day", "hour", "minute", "second", "microsecond"]:
    print(attr, "\t", getattr(today, attr))

print("Время", today.hour, ":", today.minute, sep="")

day = today.strftime("%A")
month = today.strftime("%B")
print("Дата: ", day, month, today.day)
