# =============================================================================
# ВОПРОС "ВЫБОР ПЕРЕВОДА" - слово и несколько вариантов ответа
# =============================================================================
#
# Что это в жизни: "карточка теста" с одним английским словом и четырьмя
# пронумерованными вариантами перевода, из которых верный только один.
# Карточку напечатали - и она уже не меняется (frozen=True): варианты и место
# правильного ответа остаются теми же, пока ученик думает.
#
# Раньше варианты собирала страница окна (ChoicePage). Но это правило
# упражнения, а не внешний вид, поэтому оно здесь, в core/, и проверяется
# быстрыми тестами (tests/unit/test_choice_question.py).
#
# Кто пользуется: страница "Выбор перевода" (gui/pages/study.py, ChoicePage).

import random
from dataclasses import dataclass

from core.models import Word
from core.vocabulary import Vocabulary


@dataclass(frozen=True)
class ChoiceQuestion:
    word: Word  # о каком слове вопрос
    options: tuple[str, ...]  # варианты перевода в том порядке, как их показать

    @classmethod
    def create(cls, word: Word, vocabulary: Vocabulary, size: int = 4) -> "ChoiceQuestion":
        """Составить вопрос: правильный перевод и size - 1 неправильных, вперемешку.

        Альтернативный конструктор (@classmethod): создавать вопрос нужно так,
        а не ChoiceQuestion(word, options) вручную - тогда правило "один верный
        вариант, остальные разные" выполняется всегда.
        """
        options = vocabulary.distractors(word, size - 1) + [word.ru]
        random.shuffle(options)  # иначе верный ответ всегда был бы последним
        # tuple() - кортеж нельзя изменить, как и весь вопрос.
        return cls(word, tuple(options))

    @property
    def correct_index(self) -> int:
        """Номер правильного варианта (с нуля)."""
        return self.options.index(self.word.ru)

    def is_correct(self, index: int) -> bool:
        """Верно ли выбран вариант с этим номером."""
        return index == self.correct_index
