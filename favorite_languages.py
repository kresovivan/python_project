import hello5

favorite_languages = {
    "jen":    "python",
    "sarah":  "c",
    "edward": "ruby",
    "phil":   "python",
}

for name, language in favorite_languages.items():
    print(f"{name.title()}'s favorite language is {language.title()}.")

for name in favorite_languages.keys():
    print(name.title())


