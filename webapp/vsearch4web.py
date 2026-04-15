import html
import os

from flask import Flask, render_template, request
from markupsafe import escape
from vsearch import search4letters

app = Flask(__name__)  # Создание экземпляра приложения Flask


def get_log_path():
    """Возвращает путь к файлу лога"""
    script_dir = os.path.dirname(__file__)
    return os.path.join(script_dir, "vsearch.log")


def log_request(req: "flask_request", res: str) -> None:
    with open(get_log_path(), "a") as log:
        print(req.form, req.remote_addr, req.user_agent, res, file=log, sep=" | ")


@app.route("/search4", methods=["POST"])
def do_search() -> "html":
    print(f"Текущая директория: {os.getcwd()}")
    print(f"Где лежит скрипт: {os.path.dirname(__file__)}")

    phrase = request.form["phrase"]
    letters = request.form["letters"]
    title = "Here are your results:"
    results = str(search4letters(phrase, letters))
    log_request(request, results)
    return render_template(
        "results.html",
        the_phrase=phrase,
        the_letters=letters,
        the_title=title,
        the_results=results,
    )


"""Повесим несколько декараторов на одну фунгкцию"""


@app.route("/")
@app.route("/entry")
def entry_page() -> str:
    return render_template(
        "entry.html", the_title="Welcome to search4letters on the web!"
    )


@app.route("/viewlog")
def view_the_log() -> str:
    contents = []
    with open(get_log_path()) as log:
        for line in log:
            contents.append([])
            for item in line.split("|"):
                contents[-1].append(escape(item))
    return str(contents)


"""Функция entry_page() — это обработчик URL-путей / и /entry."""

# http://127.0.0.1:5000/search4

if __name__ == "__main__":
    app.run(debug=True)  # debug=True Запускаем программу только при прямом вызове


"""Декораторы апозволяют вхять существующий код и добавить к нему дополнительное поведение.
Хотя декортаоры применимы не только к функциям, но и к классам, в основном их применяют к
функциям и называют декораторами функций
Декоратор начинается с символа @

Декоратор @app.route("/") — это синтаксический сахар, который связывает 
URL-путь с функцией-обработчиком. 
Он регистрирует функцию hello в системе маршрутизации Flask: 
когда сервер получает запрос по адресу /, автоматически вызывается функция hello, 
а её возвращённое значение отправляется клиенту.

В Python есть много встроенных декораторов и много сторонних модулей таких как Flask?
предоставляющих свои декораторы.
route один из них.

Декоратор route из Flask доступен в коде нашего web-приложения через переменную app,
созданную в предыдущей строке.

Функция декорируемая декоратором route начинается в следующей строке
, в нашем приложении это функция hello, которая делает только одно: 
возвращает сообщение Hello world from flask.

Последняя строка app.run() в программе предалагает объекту Flask 
в переменной app запустить веб-сервер, вызывая метод run.

На любые запросы с url / веб-сервер ответит сообщение Hello world from flask!,
а на запросы с другими url вернёт ошибку 404 Not Found.
Чтобы увидеть обработку ошибки в действии введите этот url  в броазуер:
http://127.0.0.1:5000/doesnthiswork.html

127.0.0.1 - - [14/Mar/2026 20:58:30] "GET / HTTP/1.1" 200 -
127.0.0.1 - - [14/Mar/2026 20:58:32] "GET / HTTP/1.1" 200 -
127.0.0.1 - - [14/Mar/2026 21:08:38] "GET /doesnthiswork.html HTTP/1.1" 404 -
127.0.0.1 - - [14/Mar/2026 21:08:50] "GET / HTTP/1.1" 200 -
127.0.0.1 - - [14/Mar/2026 21:08:50] "GET / HTTP/1.1" 200 -
127.0.0.1 - - [14/Mar/2026 21:08:51] "GET / HTTP/1.1" 200 -
127.0.0.1 - - [14/Mar/2026 21:08:53] "GET /doesnthiswork.html HTTP/1.1" 404 -
"""

"""Размещение фугкциональности в Web-приложении
Flask сделал следующее - лг предоставил механгизм, позволяющий взять
любую существующую функцию на Python и показать ее вывод в web браузере.

Чтобы расширить возможности в веб-приложении достаточно просто выбрать url 
и написать соответствующую строку с декоратором @app.route перед функцией,
выполнябщей фактическуу юработу. Давайтесделаеми это, используяфункцию search4letters.
"""

"""
Изменим функцию hello чтобы она возвращала html форму, затем изменим функцию
do_search чтоб перед вызовом функции search4letters она принимала введенные данныве
из формы и возвращала результаты в виде другой веб-страницы. 
"""
