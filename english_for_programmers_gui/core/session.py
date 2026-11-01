# =============================================================================
# ЗАНЯТИЕ (сессия) - порция слов и место, где пользователь остановился
# =============================================================================
#
# Сессия хранит не сами слова, а их английские написания (keys).
# Так её легко сохранить в JSON, а при следующем запуске восстановить
# слова из словаря по этим ключам.

from dataclasses import asdict, dataclass, field


@dataclass
class Session:
    mode: str  # какой режим: "cards", "choice", "typing"
    topic: str  # название темы (или особое значение, см. Vocabulary)
    keys: list[str]  # слова занятия (поле en)
    index: int = 0  # номер текущего слова
    right: int = 0  # верных ответов в этом занятии
    wrong: int = 0  # ошибок в этом занятии
    mistakes: list[str] = field(default_factory=list)  # слова с ошибками

    # field(default_factory=list) - у каждой сессии СВОЙ пустой список.
    # Написать просто mistakes: list = [] нельзя: один список стал бы общим
    # для всех объектов (вспомните тему про ссылки!).

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
