# Список с уникальными значениями - множество

party_goers = {"Эндрю", "Барбара", "Кэрол", "Дэвид"}
print("Тип данных party_goes", type(party_goers))

print("Идет ли Дэвид на вечеринку?", "Дэвид" in party_goers)
print("Идет ли Келли на вечеринку?", "Келли" in party_goers)

students = {"Эндрю", "Келли", "Лини", "Дэвид"}

commons = party_goers.intersection(students)

party_students = list(commons)

print("Пересечение двух список, что общего: ", party_students)
print("Первый студент из пересеченного списка: ", party_students[0])
