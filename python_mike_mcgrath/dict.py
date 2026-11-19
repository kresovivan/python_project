# Именованные списки - словари (массивы, ассоциативные массивы)

info = {"name": "Bob", "ref": "Python", "sys": "Win"}
print("Info: ", type(info))
print("Словарь: ", info)

print("Cпаравочник", info["ref"])


print("Ключи", info.keys())

del info["name"]
info["user"] = "Tom"
print("Словарь: ", info)

print("Есть ли здесь такой ключ: ", "name" in info)
