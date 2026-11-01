# =============================================================================
# ИНТЕРФЕЙС — всё, что связано с выводом на экран и вводом с клавиатуры
# =============================================================================
#
# Зачем отдельный класс? Остальной код не вызывает print() и input()
# напрямую, а просит об этом ConsoleUI. Если захочется сделать окно
# с кнопками вместо терминала — поменять придётся только этот файл.

import sys

from models import Word


class ConsoleUI:
    LINE = "─" * 64

    def __init__(self):
        # В терминале Windows русские буквы иногда выводятся «кракозябрами».
        # Переключаем ввод и вывод на UTF-8.
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdin.reconfigure(encoding="utf-8")

    def say(self, text: str = "") -> None:
        print(text)

    def ask(self, prompt: str = "") -> str:
        return input(prompt).strip()

    def header(self, text: str) -> None:
        print(f"\n{self.LINE}\n{text}\n{self.LINE}")

    def show_word(self, word: Word) -> None:
        print(f"\n  {word.en}   [{word.sound}]")
        print(f"  перевод: {word.ru}")
        if word.example:
            print(f"  пример:  {word.example}")

    def choose(self, title: str, options: list[str]) -> int | None:
        """Показать нумерованный список и вернуть индекс выбранного (с 0).

        Вернёт None, если ввели не номер или номер вне списка.
        """
        print(f"\n{title}")
        for number, option in enumerate(options, start=1):
            print(f"  {number:>2}. {option}")
        answer = self.ask("Номер: ")
        if answer.isdigit() and 1 <= int(answer) <= len(options):
            return int(answer) - 1
        if answer:
            print("Нет такого номера.")
        return None

    def result(self, right: int, total: int) -> None:
        percent = round(right / total * 100) if total else 0
        print(f"\n{self.LINE}\nИтог: {right} из {total} ({percent}%)")
        if percent == 100:
            print("Excellent! (экселент) — Отлично!")
        elif percent >= 70:
            print("Good job! (гуд джоб) — Хорошая работа!")
        else:
            print("Keep going! (кип гоуинг) — Продолжайте! Повторите карточки.")

    @staticmethod
    def bar(done: int, total: int, width: int = 20) -> str:
        """Полоска прогресса: ████░░░░░░

        @staticmethod — методу не нужен self (он не использует данные объекта),
        это просто функция, положенная внутрь класса по смыслу.
        """
        filled = round(done / total * width) if total else 0
        return "█" * filled + "░" * (width - filled)
