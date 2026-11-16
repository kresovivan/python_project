# =============================================================================
# ГРАММАТИКА - вся основная грамматика для тех, кто никогда не учил английский
# =============================================================================
#
# Что это в жизни: "тетрадь с правилами в табличках". Каждая тема - короткое
# объяснение простыми словами, одна или несколько таблиц и совет. Примеры по
# возможности из жизни программиста: файл, ошибка, программа, код.
#
# Темы разбиты на разделы (Основы, Времена, ...), как главы в учебнике:
# от самого простого к сложному. Раздел у темы записывает функция in_section().
#
# Это данные, а не логика: список TOPICS. Добавить тему - добавить ещё один
# GrammarTopic в нужный раздел, страницу менять не нужно.
# Кто пользуется: страница "Грамматика" (gui/pages/grammar.py).
# Тесты: tests/unit/test_grammar.py.

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Table:
    """Одна таблица: заголовки колонок и строки."""

    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    # Номера колонок (с нуля) с английским текстом: по щелчку его можно послушать.
    speak_columns: tuple[int, ...] = (0,)
    title: str = ""  # подпись над таблицей (необязательно)


@dataclass(frozen=True)
class GrammarTopic:
    """Одна тема: объяснение, таблицы, совет."""

    title: str  # название в списке тем: "Глагол to be: am, is, are"
    intro: str  # объяснение простыми словами
    tables: tuple[Table, ...]
    tip: str = ""  # совет или частая ошибка
    section: str = ""  # раздел-глава: "Основы", "Времена"... (ставит in_section)


def in_section(name: str, *topics: GrammarTopic) -> tuple[GrammarTopic, ...]:
    """Записать всем темам одно название раздела.

    Так раздел не нужно повторять в каждой теме. replace() создаёт копию темы
    с другим полем: сама тема "заморожена" (frozen=True), менять её нельзя.
    """
    return tuple(replace(topic, section=name) for topic in topics)


# Частая таблица: вид предложения, английский, перевод. Слушать - вторую колонку.
FORMS = ("Вид", "Английский", "Перевод")
EXAMPLES = ("Английский", "Перевод")


BASICS = in_section(
    "Основы",
    GrammarTopic(
        "Кто? Местоимения",
        "Местоимения заменяют имя: вместо \"Иван\" говорят \"он\". "
        "С них начинается почти каждое английское предложение.",
        (
            Table(
                ("Английский", "Читается", "Перевод", "Пример"),
                (
                    ("I", "ай", "я", "I am a programmer."),
                    ("you", "ю", "ты, вы", "You are right."),
                    ("he", "хи", "он (о человеке)", "He writes code."),
                    ("she", "ши", "она (о человеке)", "She tests the app."),
                    ("it", "ит", "он, она, оно (о предмете)", "It works."),
                    ("we", "уи", "мы", "We are a team."),
                    ("they", "зэй", "они", "They use Python."),
                ),
                speak_columns=(0, 3),
            ),
            Table(
                ("Кто делает", "Кого, кому", "Пример", "Перевод"),
                (
                    ("I", "me", "Help me.", "Помоги мне."),
                    ("you", "you", "I see you.", "Я вижу тебя."),
                    ("he", "him", "Call him.", "Позвони ему."),
                    ("she", "her", "Ask her.", "Спроси её."),
                    ("it", "it", "Delete it.", "Удали это."),
                    ("we", "us", "Tell us.", "Скажи нам."),
                    ("they", "them", "Fix them.", "Исправь их."),
                ),
                speak_columns=(0, 1, 2),
                title="Кого? Кому? После глагола",
            ),
            Table(
                ("Кто", "Чей", "Перевод"),
                (
                    ("I", "my", "мой"),
                    ("you", "your", "твой, ваш"),
                    ("he", "his", "его"),
                    ("she", "her", "её"),
                    ("it", "its", "его, её (о предмете)"),
                    ("we", "our", "наш"),
                    ("they", "their", "их"),
                ),
                speak_columns=(0, 1),
                title="Чей? Притяжательные слова",
            ),
        ),
        "I (я) всегда пишется с большой буквы. Программа, файл, кошка - это it, а не he или she.",
    ),
    GrammarTopic(
        "Глагол to be: am, is, are",
        "В русском говорят \"я программист\", пропуская слово \"есть\". В английском так нельзя: "
        "нужен глагол be. Он меняется: am, is или are - смотря кто.",
        (
            Table(
                ("Кто", "Утверждение", "Отрицание", "Вопрос"),
                (
                    ("I", "I am", "I am not", "Am I?"),
                    ("he, she, it", "He is", "He is not (isn't)", "Is he?"),
                    ("you, we, they", "You are", "You are not (aren't)", "Are you?"),
                ),
                speak_columns=(1, 2, 3),
            ),
            Table(
                ("Кто", "Прошедшее", "Перевод"),
                (
                    ("I, he, she, it", "I was at home.", "Я был дома."),
                    ("you, we, they", "They were busy.", "Они были заняты."),
                ),
                speak_columns=(1,),
                title="В прошлом: was, were",
            ),
            Table(
                EXAMPLES,
                (
                    ("I am a developer.", "Я разработчик."),
                    ("The file is big.", "Файл большой."),
                    ("We are in the office.", "Мы в офисе."),
                    ("It is not a bug.", "Это не ошибка."),
                    ("Is it ready?", "Это готово?"),
                ),
                title="Примеры",
            ),
        ),
        "Сокращения: I'm = I am, it's = it is, you're = you are. В разговоре почти всегда говорят коротко.",
    ),
    GrammarTopic(
        "Артикли: a, an, the",
        "Артикль - маленькое слово перед предметом. В русском артиклей нет, поэтому сначала "
        "достаточно запомнить простое правило: a - \"какой-то один\", the - \"тот самый\".",
        (
            Table(
                ("Артикль", "Когда", "Пример", "Перевод"),
                (
                    ("a", "один, любой; перед согласным звуком", "a cat", "(какая-то) кошка"),
                    ("an", "то же, но перед гласным звуком", "an ant", "(какой-то) муравей"),
                    ("the", "тот самый, о котором уже знаем", "the cat", "эта кошка"),
                    ("-", "много чего-то или вообще", "cats, water", "кошки, вода"),
                ),
                speak_columns=(2,),
            ),
            Table(
                EXAMPLES,
                (
                    ("I have a laptop. The laptop is new.", "У меня есть ноутбук. Этот ноутбук новый."),
                    ("Open the settings.", "Откройте настройки (единственные в программе)."),
                    ("She is an engineer.", "Она инженер (профессия - всегда с a или an)."),
                    ("I like music.", "Я люблю музыку (вообще - без артикля)."),
                ),
                title="Примеры",
            ),
        ),
        "Важен звук, а не буква: an hour (h не читается), но a user (звучит как \"юзер\").",
    ),
    GrammarTopic(
        "Множественное число",
        "Чтобы предметов стало много, к слову обычно добавляют -s. Есть несколько "
        "простых случаев и немного слов-исключений, их просто запоминают.",
        (
            Table(
                ("Правило", "Один", "Много"),
                (
                    ("обычно + s", "a cat", "two cats"),
                    ("после s, x, sh, ch + es", "a box", "two boxes"),
                    ("согласная + y: y меняется на ies", "a city", "two cities"),
                    ("исключение", "a man", "two men"),
                    ("исключение", "a child", "two children"),
                    ("исключение", "a mouse", "two mice"),
                    ("исключение", "a person", "two people"),
                ),
                speak_columns=(1, 2),
            ),
        ),
        "Окончание -s читается как [с] после глухих звуков (cats), как [з] после звонких (dogs) "
        "и как [из] после s, x, sh, ch (boxes).",
    ),
    GrammarTopic(
        "Этот и тот: this, that",
        "This и that показывают на предмет: this - этот (рядом), that - тот (подальше). "
        "Если предметов много - these и those.",
        (
            Table(
                ("Слово", "Сколько", "Где", "Пример", "Перевод"),
                (
                    ("this", "один", "рядом", "this file", "этот файл"),
                    ("these", "много", "рядом", "these files", "эти файлы"),
                    ("that", "один", "подальше", "that server", "тот сервер"),
                    ("those", "много", "подальше", "those servers", "те серверы"),
                ),
                speak_columns=(0, 3),
            ),
            Table(
                EXAMPLES,
                (
                    ("This is my code.", "Это мой код."),
                    ("Is that your laptop?", "Это твой ноутбук?"),
                    ("These tests are new.", "Эти тесты новые."),
                    ("Those were good days.", "То были хорошие дни."),
                ),
                title="Примеры",
            ),
        ),
        "This is ... - так начинают знакомство и объяснение: This is Ivan. This is my project.",
    ),
    GrammarTopic(
        "Чей? Притяжательный 's",
        "Чтобы сказать \"код Ивана\", к хозяину добавляют 's и ставят его впереди: Ivan's code. "
        "Сначала хозяин, потом то, что ему принадлежит.",
        (
            Table(
                ("Кто хозяин", "Как сказать", "Перевод"),
                (
                    ("один: Ivan", "Ivan's code", "код Ивана"),
                    ("один: the user", "the user's password", "пароль пользователя"),
                    ("много, на -s: the users", "the users' files", "файлы пользователей"),
                    ("много, без -s: children", "children's games", "детские игры"),
                ),
                speak_columns=(1,),
            ),
            Table(
                EXAMPLES,
                (
                    ("the name of the file", "имя файла"),
                    ("the end of the line", "конец строки"),
                    ("the top of the page", "верх страницы"),
                ),
                title="У предметов чаще говорят через of",
            ),
        ),
        "Не путайте: it's = it is, а its = его (о предмете). The file and its name - файл и его имя.",
    ),
    GrammarTopic(
        "Есть: there is, there are",
        "Когда говорят, что где-то что-то есть, начинают с there is (одно) или there are (много). "
        "\"В коде есть ошибка\" - There is a bug in the code.",
        (
            Table(
                ("Сколько", "Утверждение", "Отрицание", "Вопрос"),
                (
                    ("одно", "There is a bug.", "There is no bug.", "Is there a bug?"),
                    ("много", "There are two bugs.", "There are no bugs.", "Are there any bugs?"),
                ),
                speak_columns=(1, 2, 3),
            ),
            Table(
                EXAMPLES,
                (
                    ("There is a file on the desktop.", "На рабочем столе есть файл."),
                    ("There are 10 tests in this folder.", "В этой папке 10 тестов."),
                    ("There was an error.", "Была ошибка."),
                    ("There were many users.", "Было много пользователей."),
                ),
                title="Примеры",
            ),
        ),
        "Сокращение: there's = there is. Переводить удобно с конца: \"на столе (есть) файл\".",
    ),
    GrammarTopic(
        "Иметь: have, has",
        "\"У меня есть компьютер\" по-английски звучит как \"я имею компьютер\": "
        "I have a computer. После he, she, it - has.",
        (
            Table(
                ("Кто", "Утверждение", "Отрицание", "Вопрос"),
                (
                    ("I, you, we, they", "I have a laptop.", "I don't have a laptop.", "Do you have a laptop?"),
                    ("he, she, it", "She has a cat.", "She doesn't have a cat.", "Does she have a cat?"),
                ),
                speak_columns=(1, 2, 3),
            ),
            Table(
                EXAMPLES,
                (
                    ("I have got a question.", "У меня есть вопрос."),
                    ("He has got two monitors.", "У него два монитора."),
                    ("Have you got a minute?", "У тебя есть минутка?"),
                ),
                title="Разговорный вариант: have got",
            ),
            Table(
                EXAMPLES,
                (
                    ("have breakfast", "завтракать"),
                    ("have a break", "сделать перерыв"),
                    ("have a meeting", "проводить встречу"),
                    ("have a problem", "иметь проблему"),
                ),
                title="Устойчивые выражения",
            ),
        ),
        "В прошедшем времени для всех had: I had, she had. Вопрос: Did you have ...?",
    ),
    GrammarTopic(
        "Числа, даты и время",
        "Обычные числа отвечают на вопрос \"сколько?\": one, two. Порядковые - \"который по счёту?\": "
        "first, second. Почти все порядковые получаются добавлением -th.",
        (
            Table(
                ("Число", "Сколько", "Который"),
                (
                    ("1", "one", "first"),
                    ("2", "two", "second"),
                    ("3", "three", "third"),
                    ("4", "four", "fourth"),
                    ("5", "five", "fifth"),
                    ("10", "ten", "tenth"),
                    ("12", "twelve", "twelfth"),
                    ("20", "twenty", "twentieth"),
                    ("21", "twenty-one", "twenty-first"),
                    ("100", "one hundred", "hundredth"),
                    ("1000", "one thousand", "thousandth"),
                ),
                speak_columns=(1, 2),
            ),
            Table(
                EXAMPLES,
                (
                    ("It's five o'clock.", "Пять часов."),
                    ("It's half past two.", "Половина третьего (2:30)."),
                    ("It's a quarter to six.", "Без четверти шесть (5:45)."),
                    ("on the first of May", "первого мая"),
                    ("in twenty twenty-six", "в 2026 году"),
                ),
                title="Время и даты",
            ),
        ),
        "Годы читают парами: 1999 - nineteen ninety-nine. Точка в числе читается point: 2.5 - two point five.",
    ),
    GrammarTopic(
        "Команды: Open, Don't",
        "Чтобы попросить или приказать, просто начните с глагола: Open the file. Не нужно "
        "ни \"you\", ни окончаний. Запретить - добавить Don't впереди. Так написаны все кнопки "
        "и подсказки в программах.",
        (
            Table(
                FORMS,
                (
                    ("сделай", "Save the file.", "Сохрани файл."),
                    ("не делай", "Don't close the window.", "Не закрывай окно."),
                    ("вежливо", "Please restart the computer.", "Пожалуйста, перезагрузите компьютер."),
                    ("давай вместе", "Let's check the logs.", "Давай проверим журналы."),
                ),
                speak_columns=(1,),
            ),
            Table(
                EXAMPLES,
                (
                    ("Open", "открыть"),
                    ("Save", "сохранить"),
                    ("Cancel", "отменить"),
                    ("Delete", "удалить"),
                    ("Try again", "попробовать ещё раз"),
                    ("Click here", "нажмите здесь"),
                ),
                title="Команды в программах",
            ),
        ),
        "Let's = let us (давай, давайте). Let's go! - Пошли!",
    ),
)


DESCRIPTION = in_section(
    "Описание и количество",
    GrammarTopic(
        "Прилагательные: какой?",
        "Прилагательное описывает предмет: big, fast, new. В английском оно не меняется: "
        "big file, big files - без всяких окончаний. И стоит всегда перед предметом.",
        (
            Table(
                ("Английский", "Перевод", "Пример"),
                (
                    ("new", "новый", "a new version"),
                    ("old", "старый", "an old laptop"),
                    ("big", "большой", "a big file"),
                    ("small", "маленький", "a small bug"),
                    ("fast", "быстрый", "a fast computer"),
                    ("slow", "медленный", "a slow network"),
                    ("easy", "лёгкий", "an easy task"),
                    ("difficult", "трудный", "a difficult question"),
                    ("important", "важный", "an important update"),
                    ("empty", "пустой", "an empty folder"),
                ),
                speak_columns=(0, 2),
            ),
            Table(
                ("Мнение", "Размер", "Возраст", "Цвет", "Предмет"),
                (
                    ("a nice", "big", "new", "black", "laptop"),
                    ("an ugly", "small", "old", "red", "car"),
                ),
                speak_columns=(0, 1, 2, 3, 4),
                title="Если прилагательных несколько - в таком порядке",
            ),
        ),
        "Прилагательное может стоять и после be: The code is clean. - Код чистый.",
    ),
    GrammarTopic(
        "Сравнение: bigger, the best",
        "Чтобы сравнить, к короткому прилагательному добавляют -er (больше), а -est - самый. "
        "К длинным словам ставят more (более) и the most (самый).",
        (
            Table(
                ("Слово", "Сравнение", "Самый", "Перевод"),
                (
                    ("fast", "faster", "the fastest", "быстрый"),
                    ("big", "bigger", "the biggest", "большой"),
                    ("easy", "easier", "the easiest", "лёгкий"),
                    ("important", "more important", "the most important", "важный"),
                    ("difficult", "more difficult", "the most difficult", "трудный"),
                ),
                speak_columns=(0, 1, 2),
                title="Правильные",
            ),
            Table(
                ("Слово", "Сравнение", "Самый", "Перевод"),
                (
                    ("good", "better", "the best", "хороший"),
                    ("bad", "worse", "the worst", "плохой"),
                    ("many, much", "more", "the most", "много"),
                    ("little", "less", "the least", "мало"),
                    ("far", "farther", "the farthest", "далёкий"),
                ),
                speak_columns=(0, 1, 2),
                title="Неправильные - запомнить",
            ),
            Table(
                EXAMPLES,
                (
                    ("Python is easier than C.", "Python легче, чем C."),
                    ("This is the fastest way.", "Это самый быстрый способ."),
                    ("The new version is as fast as the old one.", "Новая версия такая же быстрая, как старая."),
                ),
                title="Примеры",
            ),
        ),
        "Than - чем: bigger than (больше, чем). Не путайте с then - потом.",
    ),
    GrammarTopic(
        "Наречия: quickly, well",
        "Наречие говорит, как делается действие. Обычно это прилагательное плюс -ly: "
        "quick - быстрый, quickly - быстро.",
        (
            Table(
                ("Прилагательное", "Наречие", "Перевод наречия"),
                (
                    ("quick", "quickly", "быстро"),
                    ("slow", "slowly", "медленно"),
                    ("careful", "carefully", "осторожно"),
                    ("easy", "easily", "легко"),
                    ("automatic", "automatically", "автоматически"),
                    ("good", "well", "хорошо"),
                    ("fast", "fast", "быстро"),
                    ("hard", "hard", "усердно"),
                ),
                speak_columns=(0, 1),
            ),
            Table(
                EXAMPLES,
                (
                    ("He is a careful programmer.", "Он внимательный программист."),
                    ("He works carefully.", "Он работает внимательно."),
                    ("The app works well.", "Приложение работает хорошо."),
                ),
                title="Примеры",
            ),
        ),
        "Частая ошибка: works good. Правильно works well. Good - какой, well - как.",
    ),
    GrammarTopic(
        "Как часто: always, never",
        "Слова частоты говорят, как часто что-то происходит. Они ставятся перед основным "
        "глаголом, но после am, is, are.",
        (
            Table(
                ("Слово", "Как часто", "Перевод"),
                (
                    ("always", "100 из 100", "всегда"),
                    ("usually", "90 из 100", "обычно"),
                    ("often", "70 из 100", "часто"),
                    ("sometimes", "50 из 100", "иногда"),
                    ("rarely", "10 из 100", "редко"),
                    ("never", "0 из 100", "никогда"),
                ),
            ),
            Table(
                ("Правило", "Пример", "Перевод"),
                (
                    ("перед глаголом", "I always test my code.", "Я всегда проверяю свой код."),
                    ("после am, is, are", "The server is never down.", "Сервер никогда не падает."),
                    ("в вопросе", "Do you often work at night?", "Ты часто работаешь ночью?"),
                    ("в конце", "I go to the gym every day.", "Я хожу в зал каждый день."),
                ),
                speak_columns=(1,),
                title="Куда ставить",
            ),
        ),
        "Never уже значит \"не\": I never use it (а не I don't never use it).",
    ),
    GrammarTopic(
        "Сколько: much, many, few",
        "Одни предметы можно посчитать (файлы, ошибки), другие нельзя (вода, время, информация). "
        "От этого зависит, как сказать \"много\" и \"мало\".",
        (
            Table(
                ("Значение", "Можно посчитать", "Нельзя посчитать"),
                (
                    ("много", "many files", "much time"),
                    ("много (в утверждении)", "a lot of files", "a lot of time"),
                    ("мало", "few files", "little time"),
                    ("немного, несколько", "a few files", "a little time"),
                    ("сколько?", "How many files?", "How much time?"),
                ),
                speak_columns=(1, 2),
            ),
            Table(
                EXAMPLES,
                (
                    ("information", "информация"),
                    ("advice", "совет"),
                    ("software", "программы"),
                    ("data", "данные"),
                    ("money", "деньги"),
                    ("help", "помощь"),
                ),
                title="Нельзя посчитать: без -s и без a",
            ),
        ),
        "Few - мало (плохо), a few - несколько (хорошо). I have a few questions - у меня есть пара вопросов.",
    ),
    GrammarTopic(
        "Some, any, no, every",
        "Some - в утверждениях (\"немного, какой-то\"), any - в вопросах и отрицаниях, no - "
        "\"никакой\". Из них складываются слова: something (что-то), anybody (кто-нибудь), "
        "nothing (ничего).",
        (
            Table(
                ("Начало", "что", "кто", "где"),
                (
                    ("some (утверждение)", "something", "somebody", "somewhere"),
                    ("any (вопрос, отрицание)", "anything", "anybody", "anywhere"),
                    ("no (нет)", "nothing", "nobody", "nowhere"),
                    ("every (все)", "everything", "everybody", "everywhere"),
                ),
                speak_columns=(1, 2, 3),
            ),
            Table(
                EXAMPLES,
                (
                    ("Something is wrong.", "Что-то не так."),
                    ("Is anybody here?", "Здесь кто-нибудь есть?"),
                    ("I don't see anything.", "Я ничего не вижу."),
                    ("Nothing works.", "Ничего не работает."),
                    ("Everything is OK.", "Всё в порядке."),
                ),
                title="Примеры",
            ),
        ),
        "В английском одно отрицание: I see nothing или I don't see anything, но не I don't see nothing.",
    ),
)


TENSES = in_section(
    "Времена",
    GrammarTopic(
        "Present Simple: обычно",
        "Настоящее простое время - о том, что происходит обычно, всегда, каждый день. "
        "Главное правило: после he, she, it к глаголу добавляется -s.",
        (
            Table(
                ("Кто", "Утверждение", "Отрицание", "Вопрос"),
                (
                    ("I, you, we, they", "I work", "I don't work", "Do you work?"),
                    ("he, she, it", "He works", "He doesn't work", "Does he work?"),
                ),
                speak_columns=(1, 2, 3),
            ),
            Table(
                EXAMPLES,
                (
                    ("I write code every day.", "Я пишу код каждый день."),
                    ("The program runs on Windows.", "Программа работает в Windows."),
                    ("She doesn't use Linux.", "Она не пользуется Linux."),
                    ("Does it work?", "Это работает?"),
                ),
                title="Примеры",
            ),
        ),
        "В вопросе и отрицании -s переезжает в does: he works, но does he work? и he doesn't work.",
    ),
    GrammarTopic(
        "Present Continuous: сейчас",
        "Настоящее длительное время - о том, что происходит прямо сейчас. "
        "Формула: am, is или are + глагол с окончанием -ing.",
        (
            Table(
                ("Кто", "Утверждение", "Отрицание", "Вопрос"),
                (
                    ("I", "I am working", "I am not working", "Am I working?"),
                    ("he, she, it", "He is reading", "He is not reading", "Is he reading?"),
                    ("you, we, they", "They are testing", "They are not testing", "Are they testing?"),
                ),
                speak_columns=(1, 2, 3),
            ),
            Table(
                ("Английский", "Перевод", "Почему"),
                (
                    ("I work in IT.", "Я работаю в IT.", "вообще, всегда - Present Simple"),
                    ("I am working now.", "Я сейчас работаю.", "прямо сейчас - Present Continuous"),
                ),
                title="Сравните",
            ),
        ),
        "Слова-подсказки: now (сейчас), right now (прямо сейчас), at the moment (в данный момент).",
    ),
    GrammarTopic(
        "Past Simple: вчера",
        "Прошедшее простое время - о том, что уже случилось. У правильных глаголов "
        "добавляется -ed. Неправильные глаголы меняются по-своему, их запоминают.",
        (
            Table(
                ("Глагол", "Прошедшее", "Перевод"),
                (
                    ("work", "worked", "работать"),
                    ("fix", "fixed", "исправлять"),
                    ("test", "tested", "проверять"),
                    ("go", "went", "идти"),
                    ("do", "did", "делать"),
                    ("have", "had", "иметь"),
                    ("write", "wrote", "писать"),
                    ("make", "made", "делать, создавать"),
                    ("find", "found", "находить"),
                    ("get", "got", "получать"),
                ),
                speak_columns=(0, 1),
                title="Первые три - правильные (+ed), остальные - неправильные",
            ),
            Table(
                FORMS,
                (
                    ("утверждение", "I fixed the bug.", "Я исправил ошибку."),
                    ("отрицание", "I didn't fix the bug.", "Я не исправил ошибку."),
                    ("вопрос", "Did you fix the bug?", "Ты исправил ошибку?"),
                ),
                speak_columns=(1,),
                title="Вопрос и отрицание - через did",
            ),
        ),
        "После did глагол возвращается в начальную форму: did you fix, а не did you fixed.",
    ),
    GrammarTopic(
        "Неправильные глаголы",
        "У большинства глаголов прошедшее время и третья форма получаются с -ed. Но самые частые "
        "глаголы неправильные: их формы просто запоминают. Третья форма нужна для Present Perfect "
        "и страдательного залога.",
        (
            Table(
                ("Начальная", "Прошедшее", "Третья форма", "Перевод"),
                (
                    ("be", "was, were", "been", "быть"),
                    ("begin", "began", "begun", "начинать"),
                    ("break", "broke", "broken", "ломать"),
                    ("bring", "brought", "brought", "приносить"),
                    ("build", "built", "built", "строить, собирать"),
                    ("buy", "bought", "bought", "покупать"),
                    ("catch", "caught", "caught", "ловить"),
                    ("choose", "chose", "chosen", "выбирать"),
                    ("come", "came", "come", "приходить"),
                    ("cost", "cost", "cost", "стоить"),
                    ("cut", "cut", "cut", "резать"),
                    ("do", "did", "done", "делать"),
                    ("draw", "drew", "drawn", "рисовать"),
                    ("drink", "drank", "drunk", "пить"),
                    ("drive", "drove", "driven", "водить машину"),
                    ("eat", "ate", "eaten", "есть"),
                    ("fall", "fell", "fallen", "падать"),
                    ("feel", "felt", "felt", "чувствовать"),
                    ("find", "found", "found", "находить"),
                    ("forget", "forgot", "forgotten", "забывать"),
                    ("get", "got", "got", "получать"),
                    ("give", "gave", "given", "давать"),
                    ("go", "went", "gone", "идти"),
                    ("have", "had", "had", "иметь"),
                    ("hear", "heard", "heard", "слышать"),
                    ("hide", "hid", "hidden", "прятать"),
                    ("keep", "kept", "kept", "хранить"),
                    ("know", "knew", "known", "знать"),
                    ("leave", "left", "left", "оставлять, уходить"),
                    ("lose", "lost", "lost", "терять"),
                    ("make", "made", "made", "делать, создавать"),
                    ("mean", "meant", "meant", "значить"),
                    ("meet", "met", "met", "встречать"),
                    ("pay", "paid", "paid", "платить"),
                    ("put", "put", "put", "класть"),
                    ("read", "read", "read", "читать"),
                    ("run", "ran", "run", "бежать, запускать"),
                    ("say", "said", "said", "сказать"),
                    ("see", "saw", "seen", "видеть"),
                    ("send", "sent", "sent", "отправлять"),
                    ("set", "set", "set", "устанавливать"),
                    ("show", "showed", "shown", "показывать"),
                    ("speak", "spoke", "spoken", "говорить"),
                    ("take", "took", "taken", "брать"),
                    ("teach", "taught", "taught", "учить кого-то"),
                    ("tell", "told", "told", "рассказывать"),
                    ("think", "thought", "thought", "думать"),
                    ("understand", "understood", "understood", "понимать"),
                    ("write", "wrote", "written", "писать"),
                ),
                speak_columns=(0, 1, 2),
            ),
        ),
        "Учите тройками вслух: go - went - gone. Щёлкайте по словам, чтобы послушать. "
        "Read во всех формах пишется одинаково, но в прошедшем читается [рэд].",
    ),
    GrammarTopic(
        "Past Continuous: делал",
        "Прошедшее длительное время - о действии, которое шло в какой-то момент в прошлом. "
        "Формула: was или were + глагол с -ing.",
        (
            Table(
                ("Кто", "Утверждение", "Отрицание", "Вопрос"),
                (
                    ("I, he, she, it", "I was working", "I wasn't working", "Was I working?"),
                    ("you, we, they", "They were testing", "They weren't testing", "Were they testing?"),
                ),
                speak_columns=(1, 2, 3),
            ),
            Table(
                EXAMPLES,
                (
                    ("I was coding at 10 pm.", "В 10 вечера я писал код."),
                    ("I was reading when the server crashed.", "Я читал, когда сервер упал."),
                    ("What were you doing yesterday?", "Что ты делал вчера?"),
                ),
                title="Примеры",
            ),
        ),
        "Часто вместе с Past Simple: длинное действие шло (was reading), и тут случилось короткое (crashed).",
    ),
    GrammarTopic(
        "Present Perfect: уже сделал",
        "Это время связывает прошлое с настоящим: действие уже случилось, и важен результат "
        "сейчас. Когда именно - не важно. Формула: have или has + третья форма глагола "
        "(с -ed или из таблицы неправильных глаголов).",
        (
            Table(
                ("Кто", "Утверждение", "Отрицание", "Вопрос"),
                (
                    ("I, you, we, they", "I have fixed it", "I haven't fixed it", "Have you fixed it?"),
                    ("he, she, it", "She has finished", "She hasn't finished", "Has she finished?"),
                ),
                speak_columns=(1, 2, 3),
            ),
            Table(
                ("Слово", "Перевод", "Пример"),
                (
                    ("already", "уже", "I have already done it."),
                    ("just", "только что", "He has just left."),
                    ("yet", "уже? (в вопросе), ещё не", "Have you finished yet?"),
                    ("ever", "когда-нибудь", "Have you ever used Linux?"),
                    ("never", "никогда", "I have never seen this error."),
                ),
                speak_columns=(0, 2),
                title="Слова-подсказки",
            ),
        ),
        "Сокращения: I've = I have, she's = she has. С точным временем (yesterday, in 2020) это "
        "время не используют - там нужен Past Simple.",
    ),
    GrammarTopic(
        "Perfect или Past Simple?",
        "Самое трудное место для русских. Простое правило: если сказано или понятно, когда "
        "(вчера, в 2020, час назад) - Past Simple. Если важен результат сейчас, а время не "
        "названо - Present Perfect.",
        (
            Table(
                ("Present Perfect", "Значение", "Past Simple", "Значение"),
                (
                    ("I have lost my key.", "ключа нет сейчас", "I lost my key yesterday.", "потерял вчера"),
                    ("I have worked here for 5 years.", "работаю до сих пор", "I worked there for 5 years.", "уже не работаю"),
                    ("Have you seen this film?", "смотрел хоть раз?", "Did you see the film last night?", "вчера вечером"),
                ),
                speak_columns=(0, 2),
            ),
        ),
        "Слова yesterday, ago, last week, in 2020 - всегда Past Simple.",
    ),
    GrammarTopic(
        "Present Perfect Continuous",
        "О действии, которое началось в прошлом и идёт до сих пор. Отвечает на вопрос "
        "\"как долго?\". Формула: have или has + been + глагол с -ing.",
        (
            Table(
                FORMS,
                (
                    ("утверждение", "I have been working for 3 hours.", "Я работаю уже 3 часа."),
                    ("утверждение", "She has been learning English since May.", "Она учит английский с мая."),
                    ("отрицание", "I haven't been sleeping well.", "Я плохо сплю в последнее время."),
                    ("вопрос", "How long have you been waiting?", "Как долго ты ждёшь?"),
                ),
                speak_columns=(1,),
            ),
        ),
        "По-русски здесь настоящее время (\"работаю уже 3 часа\"), а по-английски - это. "
        "For - в течение, since - с какого-то момента.",
    ),
    GrammarTopic(
        "Past Perfect: сделал до",
        "Предпрошедшее время - для действия, которое случилось раньше другого действия "
        "в прошлом. Формула: had + третья форма. Для всех одинаково.",
        (
            Table(
                FORMS,
                (
                    ("утверждение", "The program had crashed before I saved the file.", "Программа упала раньше, чем я сохранил файл."),
                    ("отрицание", "I hadn't seen this error before.", "Я раньше не видел этой ошибки."),
                    ("вопрос", "Had you backed up the data?", "Ты сделал резервную копию (до того)?"),
                ),
                speak_columns=(1,),
            ),
            Table(
                ("Сначала: Past Perfect", "Потом: Past Simple", "Перевод"),
                (
                    ("The meeting had started", "when I came.", "Встреча уже началась, когда я пришёл."),
                    ("She had left", "when I called.", "Она уже ушла, когда я позвонил."),
                ),
                speak_columns=(0, 1),
                title="Что было раньше",
            ),
        ),
        "Сокращение: I'd = I had. Если события идут по порядку (пришёл, сел, открыл), хватает Past Simple.",
    ),
    GrammarTopic(
        "Future Simple: сделаю",
        "Будущее простое время - о том, что будет. Формула самая простая: will + глагол. "
        "Для всех одинаково.",
        (
            Table(
                FORMS,
                (
                    ("утверждение", "I will fix it tomorrow.", "Я исправлю это завтра."),
                    ("отрицание", "It will not (won't) work.", "Это не будет работать."),
                    ("вопрос", "Will you help me?", "Ты мне поможешь?"),
                ),
                speak_columns=(1,),
            ),
        ),
        "Сокращения: I'll = I will, won't = will not.",
    ),
    GrammarTopic(
        "Going to: собираюсь",
        "Когда уже решили и собираетесь что-то сделать, говорят am, is, are + going to + глагол. "
        "Will - решение прямо сейчас или прогноз, going to - план.",
        (
            Table(
                FORMS,
                (
                    ("утверждение", "I am going to learn Python.", "Я собираюсь учить Python."),
                    ("отрицание", "We are not going to use Java.", "Мы не собираемся использовать Java."),
                    ("вопрос", "Are you going to update the app?", "Ты собираешься обновить приложение?"),
                    ("видно по признакам", "Look at the clouds. It is going to rain.", "Посмотри на тучи. Будет дождь."),
                ),
                speak_columns=(1,),
            ),
            Table(
                ("Английский", "Перевод", "Почему"),
                (
                    ("I'm going to buy a new laptop.", "Я собираюсь купить ноутбук.", "план, решили заранее"),
                    ("The phone is ringing. I'll answer it.", "Звонит телефон. Я отвечу.", "решил прямо сейчас"),
                ),
                title="Сравните: going to и will",
            ),
        ),
        "В разговоре going to часто звучит как gonna: I'm gonna fix it. Писать так в письмах не стоит.",
    ),
    GrammarTopic(
        "Future Continuous и Perfect",
        "Ещё два будущих времени. Future Continuous (will be + -ing) - буду делать в какой-то "
        "момент. Future Perfect (will have + третья форма) - уже сделаю к какому-то сроку.",
        (
            Table(
                ("Время", "Английский", "Перевод"),
                (
                    ("Future Continuous", "At 10 am I will be working.", "В 10 утра я буду работать."),
                    ("Future Continuous", "This time tomorrow we will be flying.", "Завтра в это время мы будем лететь."),
                    ("Future Perfect", "I will have finished the project by Friday.", "Я закончу проект к пятнице."),
                    ("Future Perfect", "By 2030 I will have learned English.", "К 2030 году я выучу английский."),
                ),
                speak_columns=(1,),
            ),
        ),
        "Подсказка для Future Perfect - слово by (к сроку): by Friday, by 5 pm.",
    ),
    GrammarTopic(
        "Used to: раньше делал",
        "Used to + глагол - о том, что раньше было регулярно, а теперь нет. По-русски: \"раньше я ...\".",
        (
            Table(
                FORMS,
                (
                    ("утверждение", "I used to write in Pascal.", "Раньше я писал на Паскале."),
                    ("отрицание", "I didn't use to like tests.", "Раньше я не любил тесты."),
                    ("вопрос", "Did you use to play games?", "Ты раньше играл в игры?"),
                ),
                speak_columns=(1,),
            ),
        ),
        "Не путайте с be used to (привык): I am used to working at night - я привык работать ночью.",
    ),
    GrammarTopic(
        "Все 12 времён",
        "Времён 12, но они собираются из двух вопросов: когда (настоящее, прошлое, будущее) и как "
        "(просто, длительно, завершено, длительно и завершено). Везде один глагол work - работать.",
        (
            Table(
                ("Время", "Формула", "Пример", "Перевод"),
                (
                    ("Present Simple", "глагол (+s)", "I work.", "Я работаю (обычно)."),
                    ("Present Continuous", "am, is, are + -ing", "I am working.", "Я работаю (сейчас)."),
                    ("Present Perfect", "have, has + 3-я форма", "I have worked.", "Я поработал (есть результат)."),
                    ("Present Perfect Continuous", "have, has been + -ing", "I have been working.", "Я работаю (уже давно)."),
                ),
                speak_columns=(2,),
                title="Настоящее",
            ),
            Table(
                ("Время", "Формула", "Пример", "Перевод"),
                (
                    ("Past Simple", "глагол + ed (2-я форма)", "I worked.", "Я работал (вчера)."),
                    ("Past Continuous", "was, were + -ing", "I was working.", "Я работал (в тот момент)."),
                    ("Past Perfect", "had + 3-я форма", "I had worked.", "Я поработал (до того)."),
                    ("Past Perfect Continuous", "had been + -ing", "I had been working.", "Я работал (долго до того)."),
                ),
                speak_columns=(2,),
                title="Прошлое",
            ),
            Table(
                ("Время", "Формула", "Пример", "Перевод"),
                (
                    ("Future Simple", "will + глагол", "I will work.", "Я буду работать."),
                    ("Future Continuous", "will be + -ing", "I will be working.", "Я буду работать (в тот момент)."),
                    ("Future Perfect", "will have + 3-я форма", "I will have worked.", "Я поработаю (к сроку)."),
                    ("Future Perfect Continuous", "will have been + -ing", "I will have been working.", "Я буду работать (уже долго к сроку)."),
                ),
                speak_columns=(2,),
                title="Будущее",
            ),
        ),
        "Для начала хватает четырёх: Present Simple, Present Continuous, Past Simple и Future Simple. "
        "Остальные легко узнать по формуле.",
    ),
)


SENTENCES = in_section(
    "Предложения",
    GrammarTopic(
        "Порядок слов",
        "В русском слова можно переставлять: \"код пишу я\". В английском порядок строгий: "
        "кто - что делает - что - где - когда. Поменяете местами - смысл потеряется.",
        (
            Table(
                ("Кто", "Что делает", "Что", "Где", "Когда"),
                (
                    ("I", "write", "code", "at home", "every day"),
                    ("The program", "saves", "the file", "on disk", "now"),
                    ("We", "fixed", "the bug", "in the office", "yesterday"),
                ),
                speak_columns=(0, 1, 2, 3, 4),
            ),
        ),
        "Отвечайте себе на вопросы по порядку: кто? что делает? что? где? когда?",
    ),
    GrammarTopic(
        "Вопросительные слова",
        "Чтобы спросить, ставим вопросительное слово в начало, а дальше - как в вопросе "
        "без него: Where is ...? What does ...?",
        (
            Table(
                ("Слово", "Перевод", "Пример", "Перевод примера"),
                (
                    ("What", "что, какой", "What is it?", "Что это?"),
                    ("Where", "где, куда", "Where is the file?", "Где файл?"),
                    ("When", "когда", "When will it be ready?", "Когда будет готово?"),
                    ("Why", "почему", "Why does it crash?", "Почему оно падает?"),
                    ("Who", "кто", "Who wrote this code?", "Кто написал этот код?"),
                    ("Which", "который (из)", "Which file is newer?", "Какой файл новее?"),
                    ("How", "как", "How does it work?", "Как это работает?"),
                    ("How many", "сколько (штук)", "How many errors?", "Сколько ошибок?"),
                    ("How much", "сколько (не штук)", "How much memory?", "Сколько памяти?"),
                    ("How long", "как долго", "How long does it take?", "Сколько это займёт?"),
                ),
                speak_columns=(0, 2),
            ),
        ),
        "Who wrote this code? - вопрос к \"кто\", поэтому без does и did.",
    ),
    GrammarTopic(
        "Короткие ответы: Yes, I do",
        "На вопрос \"да или нет\" англичане редко отвечают одним словом. Они повторяют "
        "вспомогательное слово из вопроса: Do you ...? - Yes, I do.",
        (
            Table(
                ("Вопрос", "Да", "Нет"),
                (
                    ("Do you like Python?", "Yes, I do.", "No, I don't."),
                    ("Does it work?", "Yes, it does.", "No, it doesn't."),
                    ("Is it ready?", "Yes, it is.", "No, it isn't."),
                    ("Are you busy?", "Yes, I am.", "No, I'm not."),
                    ("Did you save it?", "Yes, I did.", "No, I didn't."),
                    ("Can you help?", "Yes, I can.", "No, I can't."),
                    ("Have you finished?", "Yes, I have.", "No, I haven't."),
                ),
                speak_columns=(0, 1, 2),
            ),
        ),
        "Просто Yes или No звучит резковато. Yes, I do - вежливо и естественно.",
    ),
    GrammarTopic(
        "Хвостики: ..., isn't it?",
        "Хвостик в конце превращает утверждение в вопрос \"правда?\", \"не так ли?\". "
        "Правило: если предложение без \"не\", хвостик с \"не\", и наоборот.",
        (
            Table(
                ("Предложение", "Хвостик", "Перевод"),
                (
                    ("It is ready,", "isn't it?", "Готово, да?"),
                    ("You like Python,", "don't you?", "Ты ведь любишь Python?"),
                    ("She can code,", "can't she?", "Она ведь умеет программировать?"),
                    ("He didn't call,", "did he?", "Он ведь не звонил?"),
                    ("They aren't here,", "are they?", "Их ведь здесь нет?"),
                    ("Let's start,", "shall we?", "Начнём, да?"),
                ),
                speak_columns=(0, 1),
            ),
        ),
        "Особый случай: I am right, aren't I? (а не amn't I).",
    ),
    GrammarTopic(
        "Союзы: and, but, because",
        "Союзы соединяют части предложения, как в русском \"и\", \"но\", \"потому что\".",
        (
            Table(
                ("Союз", "Перевод", "Пример"),
                (
                    ("and", "и", "I opened the file and saw the error."),
                    ("but", "но", "It works, but slowly."),
                    ("or", "или", "Do you use Windows or Linux?"),
                    ("because", "потому что", "It failed because the file was missing."),
                    ("so", "поэтому", "The server was down, so I restarted it."),
                    ("when", "когда", "Call me when you are ready."),
                    ("while", "пока, в то время как", "Wait while the app is loading."),
                    ("if", "если", "If it fails, check the logs."),
                    ("although", "хотя", "Although it's old, it works."),
                    ("until", "пока не, до тех пор", "Wait until it finishes."),
                ),
                speak_columns=(0, 2),
            ),
        ),
        "После when и if о будущем ставят настоящее время: when you are ready (а не will be).",
    ),
    GrammarTopic(
        "Который: who, which, that",
        "Чтобы сказать \"человек, который ...\", \"файл, который ...\", используют who (о людях), "
        "which (о предметах) или that (о тех и других).",
        (
            Table(
                ("Слово", "О ком", "Пример", "Перевод"),
                (
                    ("who", "о людях", "The man who wrote this code left.", "Человек, который написал этот код, ушёл."),
                    ("which", "о предметах", "The file which I sent is big.", "Файл, который я отправил, большой."),
                    ("that", "о людях и предметах", "This is the bug that broke the build.", "Вот ошибка, которая сломала сборку."),
                    ("whose", "чей", "the user whose password expired", "пользователь, чей пароль истёк"),
                    ("where", "где", "the office where I work", "офис, где я работаю"),
                ),
                speak_columns=(0, 2),
            ),
        ),
        "Часто that просто пропускают: the file (that) I sent. Так говорят в разговоре.",
    ),
)


MODALS = in_section(
    "Модальные глаголы",
    GrammarTopic(
        "Can, must, should",
        "Эти слова ставятся перед глаголом и не меняются: I can, he can (без -s). "
        "После них глагол в начальной форме.",
        (
            Table(
                ("Слово", "Значение", "Пример", "Перевод"),
                (
                    ("can", "могу, умею", "I can read English.", "Я умею читать по-английски."),
                    ("can't", "не могу", "I can't open the file.", "Не могу открыть файл."),
                    ("must", "должен, обязан", "You must save your work.", "Вы должны сохранить работу."),
                    ("should", "стоит, следует (совет)", "You should write tests.", "Стоит писать тесты."),
                ),
                speak_columns=(0, 2),
            ),
        ),
        "Вопрос - переставить слово вперёд: Can you help me? Should I restart it?",
    ),
    GrammarTopic(
        "May, might, could",
        "Эти слова говорят о возможности и вежливых просьбах. Как и can, они не меняются, "
        "а после них глагол в начальной форме.",
        (
            Table(
                ("Слово", "Значение", "Пример", "Перевод"),
                (
                    ("may", "может быть", "It may take a few minutes.", "Это может занять несколько минут."),
                    ("may", "можно (разрешение)", "May I come in?", "Можно войти?"),
                    ("might", "может быть (уверенности меньше)", "It might be a bug.", "Возможно, это ошибка."),
                    ("could", "мог, умел (в прошлом)", "I could swim at five.", "Я умел плавать в пять лет."),
                    ("could", "вежливая просьба", "Could you help me?", "Не могли бы вы мне помочь?"),
                ),
                speak_columns=(0, 2),
            ),
        ),
        "Could you ...? звучит вежливее, чем Can you ...? В письмах лучше could.",
    ),
    GrammarTopic(
        "Have to, need to",
        "Have to - \"приходится, надо\" из-за обстоятельств. Need to - \"нужно\". В отличие от "
        "must, они меняются: has to, had to, will have to.",
        (
            Table(
                ("Когда", "Английский", "Перевод"),
                (
                    ("сейчас", "I have to update the system.", "Мне надо обновить систему."),
                    ("сейчас, он или она", "She has to work late.", "Ей приходится работать допоздна."),
                    ("прошлое", "We had to restart the server.", "Нам пришлось перезапустить сервер."),
                    ("будущее", "You will have to wait.", "Вам придётся подождать."),
                    ("нужно", "I need to check the logs.", "Мне нужно проверить журналы."),
                ),
                speak_columns=(1,),
            ),
            Table(
                ("Английский", "Значение"),
                (
                    ("You mustn't delete this file.", "нельзя, запрещено"),
                    ("You don't have to delete this file.", "не обязательно, можно не удалять"),
                    ("You don't need to come.", "не нужно приходить"),
                ),
                title="Не путать",
            ),
        ),
        "Mustn't - нельзя, don't have to - не надо. Разница огромная.",
    ),
)


CONSTRUCTIONS = in_section(
    "Конструкции",
    GrammarTopic(
        "-ing или to: enjoy, want",
        "Когда один глагол идёт за другим, второй принимает форму -ing или to + глагол. "
        "Какую - зависит от первого глагола, это запоминают списками.",
        (
            Table(
                ("После этих - to", "Пример", "Перевод"),
                (
                    ("want", "I want to learn English.", "Я хочу выучить английский."),
                    ("need", "You need to restart.", "Тебе нужно перезапустить."),
                    ("decide", "We decided to use Python.", "Мы решили использовать Python."),
                    ("try", "Try to open it again.", "Попробуй открыть снова."),
                    ("forget", "Don't forget to save.", "Не забудь сохранить."),
                ),
                speak_columns=(0, 1),
            ),
            Table(
                ("После этих - -ing", "Пример", "Перевод"),
                (
                    ("enjoy", "I enjoy coding.", "Мне нравится программировать."),
                    ("finish", "I finished writing the tests.", "Я закончил писать тесты."),
                    ("stop", "Stop talking.", "Перестань болтать."),
                    ("avoid", "Avoid using global variables.", "Избегайте глобальных переменных."),
                    ("mind", "Do you mind waiting?", "Вы не против подождать?"),
                ),
                speak_columns=(0, 1),
            ),
        ),
        "После предлогов всегда -ing: thank you for helping, good at programming.",
    ),
    GrammarTopic(
        "Страдательный залог",
        "Когда важно, что сделано, а не кто сделал: \"файл удалён\", \"программа написана "
        "на Python\". Формула: be (am, is, are, was, were) + третья форма глагола.",
        (
            Table(
                ("Время", "Английский", "Перевод"),
                (
                    ("настоящее", "The app is used by millions.", "Приложением пользуются миллионы."),
                    ("прошлое", "The file was deleted.", "Файл был удалён."),
                    ("прошлое", "These tests were written last year.", "Эти тесты написаны в прошлом году."),
                    ("будущее", "The bug will be fixed tomorrow.", "Ошибка будет исправлена завтра."),
                    ("уже сделано", "Your password has been changed.", "Ваш пароль изменён."),
                    ("с can", "It can't be done.", "Это невозможно сделать."),
                ),
                speak_columns=(1,),
            ),
        ),
        "Кто сделал - через by: written by Guido (написан Гвидо). Сообщения программ часто "
        "в этом залоге: File not found, Access denied.",
    ),
    GrammarTopic(
        "If: реальное условие",
        "Условное предложение состоит из двух частей: если ..., то ... . Тип 0 - то, что верно "
        "всегда. Тип 1 - реальное будущее: так и будет, если условие выполнится.",
        (
            Table(
                ("Тип", "Формула", "Пример", "Перевод"),
                (
                    ("0: всегда так", "if + настоящее, настоящее", "If you heat water to 100 degrees, it boils.", "Если нагреть воду до 100 градусов, она кипит."),
                    ("0: всегда так", "if + настоящее, настоящее", "If the battery is low, the laptop sleeps.", "Если батарея садится, ноутбук засыпает."),
                    ("1: реальное будущее", "if + настоящее, will + глагол", "If you press F5, the page will reload.", "Если нажмёшь F5, страница обновится."),
                    ("1: реальное будущее", "if + настоящее, will + глагол", "If it rains, I will stay at home.", "Если пойдёт дождь, я останусь дома."),
                ),
                speak_columns=(2,),
            ),
        ),
        "Главная ловушка: после if о будущем говорят в настоящем времени. If it rains (а не if it will rain).",
    ),
    GrammarTopic(
        "If: нереальное условие",
        "Тип 2 - мечта или то, что нереально сейчас (\"если бы у меня было ...\"). Тип 3 - "
        "сожаление о прошлом, которое уже не изменить (\"если бы я тогда ...\").",
        (
            Table(
                ("Тип", "Формула", "Пример", "Перевод"),
                (
                    ("2: нереально сейчас", "if + прошедшее, would + глагол", "If I had more time, I would learn Go.", "Если бы у меня было больше времени, я бы выучил Go."),
                    ("2: нереально сейчас", "if + were, would + глагол", "If I were you, I would update it.", "На твоём месте я бы обновил это."),
                    ("3: нереально в прошлом", "if + had + 3-я форма, would have + 3-я форма", "If I had saved the file, I wouldn't have lost it.", "Если бы я сохранил файл, я бы его не потерял."),
                    ("3: нереально в прошлом", "то же", "If you had told me, I would have helped.", "Если бы ты сказал мне, я бы помог."),
                ),
                speak_columns=(2,),
            ),
        ),
        "If I were you - устойчивое выражение для совета: were для всех, даже для I и he.",
    ),
    GrammarTopic(
        "Жаль, что: I wish",
        "I wish - \"я бы хотел\", \"жаль, что\". Время после него сдвигается на шаг в прошлое, "
        "как в нереальных условных предложениях.",
        (
            Table(
                ("О чём", "Английский", "Перевод"),
                (
                    ("сейчас", "I wish I knew English better.", "Жаль, что я не знаю английский лучше."),
                    ("сейчас", "I wish it were Friday.", "Хотелось бы, чтобы была пятница."),
                    ("о прошлом", "I wish I had saved the file.", "Жаль, что я не сохранил файл."),
                    ("раздражает", "I wish you would stop.", "Хоть бы ты перестал."),
                ),
                speak_columns=(1,),
            ),
        ),
        "По-русски \"жаль, что не знаю\" (с \"не\"), а по-английски без отрицания: I wish I knew.",
    ),
    GrammarTopic(
        "Косвенная речь",
        "Когда пересказывают чужие слова (\"он сказал, что ...\"), время в пересказе обычно "
        "сдвигается на шаг в прошлое.",
        (
            Table(
                ("Сказал", "Пересказ", "Перевод пересказа"),
                (
                    ("I am tired.", "He said (that) he was tired.", "Он сказал, что устал."),
                    ("I work here.", "She said she worked there.", "Она сказала, что работает там."),
                    ("I will help.", "He said he would help.", "Он сказал, что поможет."),
                    ("I have finished.", "She said she had finished.", "Она сказала, что закончила."),
                    ("Is it ready?", "He asked if it was ready.", "Он спросил, готово ли это."),
                    ("Close the door.", "She told me to close the door.", "Она попросила меня закрыть дверь."),
                ),
                speak_columns=(0, 1),
            ),
            Table(
                ("Было", "Стало", "Перевод"),
                (
                    ("now", "then", "сейчас, тогда"),
                    ("today", "that day", "сегодня, в тот день"),
                    ("here", "there", "здесь, там"),
                    ("tomorrow", "the next day", "завтра, на следующий день"),
                ),
                speak_columns=(0, 1),
                title="Слова тоже меняются",
            ),
        ),
        "Say - просто сказать (said that ...), tell - сказать кому-то (told me that ...).",
    ),
    GrammarTopic(
        "Инверсия: Never have I",
        "Иногда для выразительности слова меняют местами, как в вопросе. Это книжный и деловой "
        "стиль: встречается в документации и письмах. Самому говорить так не обязательно, "
        "но узнавать полезно.",
        (
            Table(
                ("Обычно", "С инверсией", "Перевод"),
                (
                    ("I have never seen such a bug.", "Never have I seen such a bug.", "Никогда я не видел такой ошибки."),
                    ("You should not change this file.", "Under no circumstances should you change this file.", "Ни в коем случае не меняйте этот файл."),
                    ("If you have any questions, ...", "Should you have any questions, ...", "Если у вас будут вопросы, ..."),
                    ("If I had known, ...", "Had I known, ...", "Если бы я знал, ..."),
                    ("It had just started when it crashed.", "Hardly had it started when it crashed.", "Едва оно запустилось, как упало."),
                ),
                speak_columns=(0, 1),
            ),
        ),
        "Should you have any questions, please contact us - частая фраза в конце деловых писем.",
    ),
)


PREPOSITIONS = in_section(
    "Предлоги и фразовые глаголы",
    GrammarTopic(
        "Предлоги: in, on, at",
        "Три самых частых предлога. В них путаются все, поэтому достаточно запомнить "
        "основные случаи из таблицы.",
        (
            Table(
                ("Предлог", "Место", "Время"),
                (
                    ("in", "внутри: in the folder, in the box", "месяц, год: in May, in 2026"),
                    ("on", "на поверхности: on the desk, on the screen", "день: on Monday"),
                    ("at", "в точке: at home, at work", "точное время: at 5 o'clock"),
                ),
            ),
        ),
        "Для программиста: in the code (в коде), on the server (на сервере), at line 10 (в строке 10).",
    ),
    GrammarTopic(
        "Куда: to, into, from",
        "Предлоги движения отвечают на вопросы \"куда?\" и \"откуда?\".",
        (
            Table(
                ("Предлог", "Значение", "Пример", "Перевод"),
                (
                    ("to", "куда, к", "Go to the settings.", "Перейдите в настройки."),
                    ("from", "откуда, от", "Download it from the site.", "Скачайте это с сайта."),
                    ("into", "внутрь", "Copy it into the folder.", "Скопируйте это в папку."),
                    ("out of", "изнутри наружу", "Get out of the loop.", "Выйди из цикла."),
                    ("onto", "на (поверхность)", "Drag the file onto the desktop.", "Перетащите файл на рабочий стол."),
                    ("through", "через, сквозь", "The data goes through the network.", "Данные идут через сеть."),
                    ("over", "над", "Move the mouse over the button.", "Наведите мышь на кнопку."),
                    ("under", "под", "The cable is under the desk.", "Кабель под столом."),
                ),
                speak_columns=(0, 2),
            ),
        ),
        "Домой - home без to: go home. На работу - с to: go to work.",
    ),
    GrammarTopic(
        "Время: for, since, ago",
        "Эти слова отвечают на вопросы \"как долго?\" и \"когда?\". Их легко перепутать, "
        "поэтому смотрите на таблицу.",
        (
            Table(
                ("Слово", "Значение", "Пример", "Перевод"),
                (
                    ("for", "в течение (сколько)", "I have worked here for two years.", "Я работаю здесь два года."),
                    ("since", "с (какого момента)", "I have worked here since 2024.", "Я работаю здесь с 2024 года."),
                    ("ago", "назад", "I started two years ago.", "Я начал два года назад."),
                    ("during", "во время (чего)", "Don't turn it off during the update.", "Не выключайте во время обновления."),
                    ("until", "до (какого момента)", "Wait until 5 pm.", "Подождите до 17:00."),
                    ("by", "к (сроку)", "Finish it by Friday.", "Закончите к пятнице."),
                    ("in", "через (сколько)", "I'll be back in 10 minutes.", "Вернусь через 10 минут."),
                ),
                speak_columns=(0, 2),
            ),
        ),
        "For + срок (for 3 days), since + точка (since Monday). Ago ставится после срока: 3 days ago.",
    ),
    GrammarTopic(
        "Фразовые глаголы",
        "Фразовый глагол - глагол плюс маленькое слово (up, in, out, off), и вместе у них "
        "новый смысл. В компьютерных программах они повсюду.",
        (
            Table(
                ("Глагол", "Перевод", "Пример"),
                (
                    ("log in", "войти (в систему)", "Log in with your password."),
                    ("log out", "выйти", "Don't forget to log out."),
                    ("sign up", "зарегистрироваться", "Sign up for free."),
                    ("set up", "настроить, установить", "Set up the environment."),
                    ("back up", "сделать резервную копию", "Back up your data."),
                    ("shut down", "выключить", "Shut down the computer."),
                    ("turn on", "включить", "Turn on dark mode."),
                    ("turn off", "выключить", "Turn off notifications."),
                    ("look up", "найти (в справочнике)", "Look up the word in a dictionary."),
                    ("find out", "узнать, выяснить", "Find out why it fails."),
                    ("give up", "сдаться, бросить", "Don't give up!"),
                    ("run out of", "закончиться", "We ran out of memory."),
                ),
                speak_columns=(0, 2),
            ),
        ),
        "Слитно пишется существительное: a backup (резервная копия), a setup, a login. "
        "Раздельно - глагол: back up, set up, log in.",
    ),
)


# Все темы по порядку: от простого к сложному. Номер темы в этом кортеже
# сохраняется в настройках ("grammar_index") и показывается в оглавлении.
TOPICS: tuple[GrammarTopic, ...] = (
    *BASICS,
    *DESCRIPTION,
    *TENSES,
    *SENTENCES,
    *MODALS,
    *CONSTRUCTIONS,
    *PREPOSITIONS,
)
