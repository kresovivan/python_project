def echo(user, lang, sys):
    print("Пользователь: ", user, "Язык: ", lang, "Платформа: ", sys)


echo("Mike", "Python", "Windows")
echo(lang="Python", sys="Mac OS", user="Ivan")


def mirror(user="Carole", lang="Python"):
    print("Пользователь:", user, "Язык:", lang)


mirror()
mirror(lang="Java")
mirror("Tony")
mirror("Susan", " C++")
