# =============================================================================
# ЗАНЯТИЕ - логика одного режима (карточки, выбор, написание) без интерфейса
# =============================================================================
#
# Раньше эта логика жила прямо в странице окна вперемешку с кнопками.
# Теперь страница только показывает слова и передаёт ответы, а Lesson решает:
#   - какие слова взять для занятия (из темы, все, только слабые);
#   - какое слово сейчас;
#   - как засчитать ответ и где сохранить место остановки.
# Такой класс легко проверить без окна и легко поменять правила.

import random

from core.models import Word
from core.progress import WEAK, Progress
from core.session import Session
from core.settings import Settings
from core.vocabulary import Vocabulary

ALL_TOPICS = "Все темы"
WEAK_WORDS = "Слабые слова (работа над ошибками)"


class Lesson:
    SIZE = 20  # слов в одном занятии

    def __init__(self, mode: str, vocabulary: Vocabulary, progress: Progress, settings: Settings):
        self.mode = mode  # "cards", "choice" или "typing"
        self._vocabulary = vocabulary
        self._progress = progress
        self._settings = settings
        self.session: Session | None = None
        # Список тем для выбора: два особых пункта + темы из словаря.
        self.topics: list[str] = [ALL_TOPICS, WEAK_WORDS] + vocabulary.topics()

    # --- темы -----------------------------------------------------------------

    def known_topic(self, topic: str) -> str:
        """Тема, если она есть в списке, иначе "Все темы".

        Нужно, если в настройках сохранилась тема, которую потом
        переименовали или удалили из файлов data/.
        """
        return topic if topic in self.topics else ALL_TOPICS

    @property
    def last_topic(self) -> str:
        return self.known_topic(self._settings.get("last_topic", ALL_TOPICS))

    def remember_topic(self, topic: str) -> None:
        self._settings.set("last_topic", topic)

    def neighbour_topic(self, topic: str, step: int) -> str:
        """Соседняя тема в списке: step=1 - следующая, -1 - предыдущая (по кругу)."""
        index = self.topics.index(self.known_topic(topic))
        return self.topics[(index + step) % len(self.topics)]

    def words_for(self, topic: str) -> list[Word]:
        topic = self.known_topic(topic)
        if topic == ALL_TOPICS:
            return self._vocabulary.all_words()
        if topic == WEAK_WORDS:
            return [w for w in self._vocabulary.all_words() if self._progress.status(w) == WEAK]
        return self._vocabulary.words(topic)

    # --- начало занятия -------------------------------------------------------

    def start(self, topic: str) -> bool:
        """Новое занятие по теме. False - в теме нет подходящих слов."""
        self.remember_topic(topic)
        words = self.words_for(topic)
        if not words:
            return False
        picked = self._progress.pick(words, self.SIZE)
        self._begin(Session(mode=self.mode, topic=self.known_topic(topic), keys=[w.en for w in picked]))
        return True

    def retry_mistakes(self) -> bool:
        """Новое занятие только из слов, в которых ошиблись в этом занятии."""
        if not (self.session and self.session.mistakes):
            return False
        keys = list(dict.fromkeys(self.session.mistakes))  # убрать повторы, сохранив порядок
        random.shuffle(keys)
        self._begin(Session(mode=self.mode, topic=self.session.topic, keys=keys))
        return True

    def restore(self) -> bool:
        """Продолжить сохранённое занятие с места остановки. False - его нет."""
        saved = self._settings.session(self.mode)
        if saved is None:
            return False
        saved.topic = self.known_topic(saved.topic)
        self.session = saved
        return True

    def forget(self) -> None:
        """Убрать занятие с экрана (сохранённое в настройках остаётся)."""
        self.session = None

    def _begin(self, session: Session) -> None:
        self.session = session
        self._settings.save_session(session)

    # --- ход занятия ----------------------------------------------------------

    @property
    def active(self) -> bool:
        """Идёт ли сейчас незаконченное занятие."""
        return self.session is not None and not self.session.finished

    def current_word(self) -> Word | None:
        """Текущее слово или None, если занятие закончено."""
        session = self.session
        # Пропускаем слова, которых больше нет в словаре (например, удалили из файла).
        while not session.finished and self._vocabulary.get(session.keys[session.index]) is None:
            session.index += 1
        if session.finished:
            self._settings.save_session(session)  # законченное занятие удаляется из сохранённых
            return None
        return self._vocabulary.get(session.keys[session.index])

    def answer(self, word: Word, is_right: bool) -> None:
        """Засчитать ответ и СРАЗУ сохранить место остановки.

        Номер слова увеличивается здесь, а не при переходе к следующему слову:
        если закрыть программу, пока на экране подсветка ответа, при
        следующем запуске ответ не засчитается второй раз.
        """
        session = self.session
        self._progress.record(word, is_right)
        if is_right:
            session.right += 1
        else:
            session.wrong += 1
            session.mistakes.append(word.en)
        session.index += 1
        self._settings.save_session(session)
