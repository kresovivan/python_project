# =============================================================================
# ЗАНЯТИЕ (сессия) - порция слов и место, где пользователь остановился
# =============================================================================
#
# Что это в жизни: "листок с заданием и счётом". На листке 20 слов по
# порядку, отметка, до какого слова дошли, и сколько ответов было верных
# и неверных. Листок можно отложить (сохранить в state.json) и завтра
# продолжить с того же места.
#
# Сессия хранит не сами слова, а их английские написания (keys).
# Так её легко сохранить в JSON, а при следующем запуске восстановить
# слова из словаря по этим ключам.
#
# Кто пользуется: Lesson (core/lesson.py) создаёт сессию и передаёт ей
# ответы, Settings (core/settings.py) сохраняет её, страницы показывают счёт.

from dataclasses import asdict, dataclass, field

# Режимы занятий. Это и ключи страниц в меню, и имена сохранённых занятий
# в state.json. Строки менять нельзя: у пользователя уже сохранены занятия
# с такими именами, после переименования они перестанут находиться.
CARDS = "cards"  # карточки "знаю / не знаю"
CHOICE = "choice"  # выбор перевода из вариантов
TYPING = "typing"  # написание слова по-английски
STUDY_MODES = (CARDS, CHOICE, TYPING)  # в порядке меню

# Оценка за занятие (что написать на экране итогов - решает страница окна).
EXCELLENT = "excellent"  # всё верно
GOOD = "good"  # верно не меньше GOOD_FROM процентов
KEEP_GOING = "keep_going"  # остальное
GOOD_FROM = 70


@dataclass
class Session:
    mode: str  # какой режим: CARDS, CHOICE или TYPING
    topic: str  # название темы (или особое значение, см. core/lesson.py)
    keys: list[str]  # слова занятия (поле en)
    index: int = 0  # номер текущего слова
    right: int = 0  # верных ответов в этом занятии
    wrong: int = 0  # ошибок в этом занятии
    mistakes: list[str] = field(default_factory=list)  # слова с ошибками

    # field(default_factory=list) - у каждой сессии СВОЙ пустой список.
    # Написать просто mistakes: list = [] нельзя: один список стал бы общим
    # для всех объектов (вспомните тему про ссылки!).

    # --- ход занятия ---------------------------------------------------------
    # Счёт меняет только сама сессия, через record_answer(). Другие классы
    # не пишут session.right += 1 снаружи: так правило "как считать ответ"
    # записано в одном месте (принцип ООП "инкапсуляция").

    def record_answer(self, is_right: bool) -> None:
        """Засчитать ответ на текущее слово и перейти к следующему."""
        if self.finished:
            raise ValueError("Занятие закончено: отвечать больше не на что")
        if is_right:
            self.right += 1
        else:
            self.wrong += 1
            self.mistakes.append(self.keys[self.index])
        self.index += 1

    def skip_word(self) -> None:
        """Перейти к следующему слову без ответа (слово удалили из словаря)."""
        if self.finished:
            raise ValueError("Занятие закончено: пропускать нечего")
        self.index += 1

    @property
    def current_key(self) -> str | None:
        """Английское слово, на котором остановились (None - занятие закончено)."""
        return None if self.finished else self.keys[self.index]

    # --- что показать на экране ------------------------------------------------

    @property
    def total(self) -> int:
        return len(self.keys)

    @property
    def finished(self) -> bool:
        return self.index >= self.total

    @property
    def answered(self) -> int:
        return self.right + self.wrong

    @property
    def percent(self) -> int:
        """Процент верных ответов (0-100)."""
        return round(self.right / self.answered * 100) if self.answered else 0

    @property
    def fraction(self) -> float:
        """Доля пройденного: от 0.0 до 1.0 (для полоски прогресса)."""
        return self.index / self.total if self.total else 0.0

    @property
    def rating(self) -> str:
        """Оценка за занятие: EXCELLENT, GOOD или KEEP_GOING."""
        if self.percent == 100:
            return EXCELLENT
        if self.percent >= GOOD_FROM:
            return GOOD
        return KEEP_GOING

    # --- сохранение ----------------------------------------------------------

    def to_dict(self) -> dict:
        # asdict() превращает dataclass в обычный словарь - его можно записать в JSON.
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        """Создать сессию из словаря.

        @classmethod получает не объект (self), а сам класс (cls).
        Так делают 'альтернативные конструкторы': Session.from_dict(...).
        """
        return cls(**data)
