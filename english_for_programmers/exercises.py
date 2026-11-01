# =============================================================================
# УПРАЖНЕНИЯ — каждый режим тренажёра это отдельный класс
# =============================================================================
#
# Все упражнения наследуются от одного родителя Exercise.
# Родитель задаёт ОБЩИЙ вид: у каждого упражнения есть title (название
# в меню) и метод run() (запуск). Как именно работает run() — решает
# каждый наследник сам. Это и есть полиморфизм: меню вызывает
# exercise.run(), не зная, какое именно упражнение перед ним.
#
#   Exercise (абстрактный)
#   ├── TopicExercise (абстрактный: умеет выбирать тему и слова)
#   │   ├── Cards        — карточки
#   │   ├── ChoiceQuiz   — тест EN → RU с вариантами
#   │   └── TypingQuiz   — тест RU → EN, ввод слова
#   ├── ErrorReading     — читаем ошибки Python
#   ├── Review           — работа над ошибками
#   ├── Search           — поиск слова в словаре
#   └── Stats            — прогресс

import random
from abc import ABC, abstractmethod

from models import ErrorMessage, Word
from progress import Progress
from ui import ConsoleUI
from vocabulary import Vocabulary


class Exercise(ABC):
    """Общий родитель всех режимов.

    ABC (Abstract Base Class) — «абстрактный класс»: создать объект
    самого Exercise нельзя, только его наследников.
    """

    title = "Упражнение"  # атрибут класса — наследники его переопределяют

    def __init__(self, vocabulary: Vocabulary, progress: Progress, ui: ConsoleUI):
        self.vocabulary = vocabulary
        self.progress = progress
        self.ui = ui

    @abstractmethod
    def run(self) -> None:
        """Запустить упражнение. Каждый наследник ОБЯЗАН написать свой run()."""


class TopicExercise(Exercise):
    """Упражнение по словам выбранной темы, порциями по SESSION_SIZE слов."""

    SESSION_SIZE = 20

    def select_words(self) -> list[Word]:
        """Спросить тему и подобрать слова для занятия (пустой список — отмена)."""
        topics = self.vocabulary.topics()
        options = [f"{name} ({len(self.vocabulary.words(name))} слов)" for name in topics]
        options.append(f"Все темы вместе ({len(self.vocabulary)} слов)")

        index = self.ui.choose("Выберите тему:", options)
        if index is None:
            return []
        if index == len(topics):
            words = self.vocabulary.all_words()
        else:
            words = self.vocabulary.words(topics[index])
        return self.progress.pick(words, self.SESSION_SIZE)

    def run(self) -> None:
        words = self.select_words()
        if words:
            self.run_on(words)

    @abstractmethod
    def run_on(self, words: list[Word]) -> None:
        """Провести упражнение на готовом списке слов."""

    @staticmethod
    def normalize(text: str) -> str:
        """Привести ответ к простому виду: регистр, пробелы, знаки — не важны.

        "  It Doesn’t work! " -> "it doesnt work"
        """
        text = text.lower().strip()
        for ch in "!?.,'’`\"":
            text = text.replace(ch, "")
        return " ".join(text.split())


class Cards(TopicExercise):
    title = "Карточки (новые слова)"

    def run_on(self, words: list[Word]) -> None:
        self.ui.header(f"Карточки: {len(words)} слов. Enter — дальше, q — выход.")
        for number, word in enumerate(words, start=1):
            self.ui.say(f"\n[{number}/{len(words)}]")
            self.ui.show_word(word)
            if self.ui.ask() == "q":
                break


class ChoiceQuiz(TopicExercise):
    title = "Тест: английский → русский (выбор)"

    def run_on(self, words: list[Word]) -> None:
        self.ui.header("Выберите перевод. q — выход.")
        right = 0
        for number, word in enumerate(words, start=1):
            options = self.vocabulary.distractors(word) + [word.ru]
            random.shuffle(options)

            self.ui.say(f"\n[{number}/{len(words)}]  {word.en}   [{word.sound}]")
            for i, option in enumerate(options, start=1):
                self.ui.say(f"   {i}. {option}")

            answer = self.ui.ask("Ваш ответ (1-4): ")
            if answer == "q":
                return
            is_right = answer in ("1", "2", "3", "4") and options[int(answer) - 1] == word.ru
            if is_right:
                right += 1
                self.ui.say("  ✔ Right! (райт) — Верно!")
            else:
                self.ui.say(f"  ✘ Wrong (ронг). Правильно: {word.ru}")
                if word.example:
                    self.ui.say(f"    пример: {word.example}")
            self.progress.record(word, is_right)
        self.ui.result(right, len(words))


class TypingQuiz(TopicExercise):
    title = "Тест: русский → английский (ввод)"

    def run_on(self, words: list[Word]) -> None:
        self.ui.header("Напишите по-английски. ? — подсказка, q — выход.")
        right = 0
        for number, word in enumerate(words, start=1):
            self.ui.say(f"\n[{number}/{len(words)}]  {word.ru}")
            answer = self.ui.ask("> ")
            if answer == "q":
                return
            if answer == "?":
                self.ui.say(f"  подсказка: {self.hint(word.answer)}   [{word.sound}]")
                answer = self.ui.ask("> ")

            is_right = self.normalize(answer) == self.normalize(word.answer)
            if is_right:
                right += 1
                self.ui.say("  ✔ Right! — Верно!")
            else:
                self.ui.say(f"  ✘ Правильно: {word.en}   [{word.sound}]")
            self.progress.record(word, is_right)
        self.ui.result(right, len(words))

    @staticmethod
    def hint(text: str) -> str:
        """Первая буква, остальные буквы — прочерки, пробелы сохраняются.

        "Can you" -> "C _ _   _ _ _"
        """
        result = text[0]
        for ch in text[1:]:
            if ch == " ":
                result += "   "
            elif ch.isalpha():
                result += " _"
            else:
                result += " " + ch
        return result


class ErrorReading(Exercise):
    title = "Читаем ошибки Python"

    def __init__(self, vocabulary, progress, ui, errors: list[ErrorMessage]):
        # super() — вызвать __init__ родителя, чтобы он сохранил
        # vocabulary, progress и ui. Потом добавляем своё поле errors.
        super().__init__(vocabulary, progress, ui)
        self.errors = errors

    def run(self) -> None:
        errors = self.errors.copy()
        random.shuffle(errors)
        self.ui.header("Настоящие ошибки Python. Попробуйте понять сами, потом Enter. q — выход.")
        for number, error in enumerate(errors, start=1):
            self.ui.say(f"\n[{number}/{len(errors)}]  {error.message}")
            if self.ui.ask("  Подумайте... (Enter — перевод) ") == "q":
                return
            self.ui.say(f"  перевод:    {error.ru}")
            self.ui.say(f"  слова:      {error.words}")
            self.ui.say(f"  что делать: {error.hint}")


class Review(Exercise):
    title = "Работа над ошибками"

    def run(self) -> None:
        weak = [w for w in self.vocabulary.all_words() if self.progress.is_weak(w)]
        if not weak:
            self.ui.say("\nСлов для повторения нет. Сначала пройдите тесты.")
            return

        random.shuffle(weak)
        weak = weak[: TopicExercise.SESSION_SIZE]
        self.ui.say(f"\nСлов для повторения: {len(weak)}. Сначала посмотрим их:")
        for word in weak:
            self.ui.show_word(word)
        if self.ui.ask("\nEnter — начать проверку, q — выход ") == "q":
            return
        # Используем готовое упражнение TypingQuiz вместо того, чтобы
        # писать проверку заново (композиция: один объект использует другой).
        TypingQuiz(self.vocabulary, self.progress, self.ui).run_on(weak)


class Search(Exercise):
    title = "Найти слово (словарь)"

    def run(self) -> None:
        self.ui.header("Поиск по-английски или по-русски. Пустая строка — выход.")
        while True:
            text = self.ui.ask("\nНайти: ")
            if not text:
                return
            found = self.vocabulary.search(text)
            if not found:
                self.ui.say("  Ничего не найдено.")
            for word in found[:15]:
                self.ui.say(f"  {word.en:<24} [{word.sound}]  —  {word.ru}   ({word.topic})")
            if len(found) > 15:
                self.ui.say(f"  ... и ещё {len(found) - 15}. Уточните запрос.")


class Stats(Exercise):
    title = "Мой прогресс"

    def run(self) -> None:
        self.ui.header("Мой прогресс")
        topics = self.vocabulary.topics()
        width = max(len(topic) for topic in topics)  # ширина колонки — по самой длинной теме
        total_learned = 0
        for topic in topics:
            words = self.vocabulary.words(topic)
            learned = sum(1 for w in words if self.progress.is_learned(w))
            total_learned += learned
            bar = self.ui.bar(learned, len(words))
            self.ui.say(f"  {topic:<{width}} {bar} {learned:>4}/{len(words)}")

        total = len(self.vocabulary)
        self.ui.say(f"\n  {'ВСЕГО':<{width}} {self.ui.bar(total_learned, total)} {total_learned:>4}/{total}")
        self.ui.say(f"\nСлово выучено после {Progress.LEARNED_AFTER} верных ответов (и если их больше, чем ошибок).")
