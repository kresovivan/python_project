# =============================================================================
# ТРЕНАЖЁР АНГЛИЙСКОГО ДЛЯ ПРОГРАММИСТОВ — точка входа
# =============================================================================
#
# Запуск: откройте этот файл в VS Code и нажмите ▷ (Run Python File).
#
# Устройство программы (каждый класс — в своём файле):
#
#   trainer.py     App          — собирает всё вместе и показывает меню
#   models.py      Word, ErrorMessage — данные одного слова / одной ошибки
#   vocabulary.py  Vocabulary   — загружает слова из папки data/
#   progress.py    Progress     — статистика ответов (progress.json)
#   ui.py          ConsoleUI    — ввод и вывод в терминале
#   exercises.py   Exercise и наследники — режимы тренажёра
#   errors_data.py ERRORS       — сообщения об ошибках Python
#   data/*.txt     сами слова, по темам
#
# Чтобы добавить слова — допишите строки в файлы data/*.txt.
# Чтобы добавить новый режим — создайте класс-наследник Exercise
# и добавьте его в список self.exercises ниже.

from pathlib import Path

from errors_data import ERRORS
from exercises import Cards, ChoiceQuiz, ErrorReading, Review, Search, Stats, TypingQuiz
from progress import Progress
from ui import ConsoleUI
from vocabulary import Vocabulary


class App:
    """Приложение: создаёт все объекты и крутит главное меню."""

    def __init__(self):
        base = Path(__file__).parent  # папка, где лежит эта программа
        self.ui = ConsoleUI()
        self.vocabulary = Vocabulary(base / "data")
        self.progress = Progress(base / "progress.json")

        # Общие «инструменты», которые нужны каждому упражнению.
        tools = (self.vocabulary, self.progress, self.ui)

        # Список режимов. Порядок в списке = порядок в меню.
        # *tools — распаковка кортежа в аргументы: Cards(vocabulary, progress, ui)
        self.exercises = [
            Cards(*tools),
            ChoiceQuiz(*tools),
            TypingQuiz(*tools),
            ErrorReading(*tools, errors=ERRORS),
            Review(*tools),
            Search(*tools),
            Stats(*tools),
        ]

    def run(self) -> None:
        self.ui.header(
            "  ENGLISH FOR PROGRAMMERS — английский для программистов\n"
            f"  В словаре {len(self.vocabulary)} слов в {len(self.vocabulary.topics())} темах"
        )
        while True:
            self.ui.say("\nMenu (меню) — Меню:")
            for number, exercise in enumerate(self.exercises, start=1):
                self.ui.say(f"  {number}. {exercise.title}")
            self.ui.say("  0. Exit (экзит) — Выход")

            choice = self.ui.ask("Выберите режим: ")
            if choice == "0":
                self.ui.say("Goodbye! (гудбай) — До свидания!")
                return
            if choice.isdigit() and 1 <= int(choice) <= len(self.exercises):
                # Полиморфизм: не важно, какой это режим — у всех есть run().
                self.exercises[int(choice) - 1].run()
            else:
                self.ui.say(f"Нет такого пункта. Введите число от 0 до {len(self.exercises)}.")


# Этот блок срабатывает, только когда файл запускают напрямую.
if __name__ == "__main__":
    try:
        App().run()
    except (KeyboardInterrupt, EOFError):
        # Ctrl+C или закрытый ввод — выходим без длинной ошибки.
        print("\nGoodbye! — До свидания!")
