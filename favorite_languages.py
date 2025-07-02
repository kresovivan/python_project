favorite_languages = {
    "jen":    "python",
    "sarah":  "c",
    "edward": "ruby",
    "phil":   "python",
    "raul":   "python",
}

for name, language in favorite_languages.items():
    print(f"{name.title()}'s favorite language is {language.title()}.")

for name in favorite_languages.keys():
    print(name.title())


friends = ["phil", "sarah"]
for name in favorite_languages.keys():
    print(name.title())

    if name in friends:
        language = favorite_languages[name].title()
        print(f"\t{name.title()}, I see you love {language}!")

for name in sorted(favorite_languages.keys()):
    print(f"{name.title()}, thank you for taking the poll")

for name in set(favorite_languages.values()):
    print(f"{name.title()}")

favorite_languages = {
    "jen":    ["python", "ruby"],
    "sarah":  ["c", "c++", "pascal"],
    "edward": ["ruby"],
    "phil":   ["python"],
    "raul":   ["python"],
}

for name, languages in favorite_languages.items():
    if len(languages) > 1:
        print(f"\n{name.title()}'s favorite languages are:")
        for language in languages:
            print(f"\t{language.title()}")
    else:
        print(f"\n{name.title()}'s favorite language is {languages[0].title()}")

