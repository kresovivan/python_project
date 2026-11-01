# =============================================================================
# ЗАНЯТИЕ - логика одного режима (карточки, выбор, написание) без интерфейса
# =============================================================================
#
# Что это в жизни: "учитель" одного упражнения. Он выбирает слова для
# занятия, показывает их по одному, принимает ответы, записывает их в
# дневник (Progress) и делает закладку (Settings), чтобы завтра продолжить.
#
# Кто с кем связан:
#   Lesson берёт слова из Vocabulary (книга),
#          ведёт счёт в Session (листок с заданием),
#          записывает ответы в Progress (дневник),
#          сохраняет место остановки через Settings (закладка).
#   Страница окна (gui/pages/study.py) только показывает слово и передаёт
#   ответ: lesson.answer(True). Поэтому всю логику занятия проверяют быстрые
#   тесты без окна (tests/unit/test_lesson.py).
#
# Правило "раздели команды и вопросы":
#   вопросы (current_word, active, last_topic) только отвечают и ничего не меняют;
#   команды (start, restore, answer, retry_mistakes) меняют занятие и сохраняют его.

import random

from core.models import Word
from core.progress import WEAK, Progress
from core.session import Session
from core.settings import Settings
from core.vocabulary import Vocabulary

# Особые пункты в списке тем: не тема из словаря, а правило подбора слов.
ALL_TOPICS = "Все темы"
WEAK_WORDS = "Слабые слова (работа над ошибками)"


class Lesson:
    SIZE = 20  # слов в одном занятии

    def __init__(self, mode: str, vocabulary: Vocabulary, progress: Progress, settings: Settings):
        self.mode = mode  # CARDS, CHOICE или TYPING (core/session.py)
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

    # --- команды: начать, продолжить, ответить -----------------------------------

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
        self._skip_missing_words()
        return True

    def answer(self, is_right: bool) -> None:
        """Засчитать ответ на ТЕКУЩЕЕ слово и СРАЗУ сохранить место остановки.

        Слово не передаётся: ответить можно только на то слово, которое сейчас
        на экране. Так счёт не собьётся, даже если вызвать answer() по ошибке
        с чужим словом.

        Номер слова увеличивается здесь, а не при переходе к следующему слову:
        если закрыть программу, пока на экране подсветка ответа, при
        следующем запуске ответ не засчитается второй раз.
        """
        word = self.current_word()
        if word is None:
            raise ValueError("Занятие закончено: отвечать больше не на что")
        self._progress.record(word, is_right)
        self.session.record_answer(is_right)  # счёт ведёт сама сессия
        self._skip_missing_words()

    def forget(self) -> None:
        """Убрать занятие с экрана (сохранённое в настройках остаётся)."""
        self.session = None

    # --- вопросы: только отвечают, ничего не меняют --------------------------------

    @property
    def active(self) -> bool:
        """Идёт ли сейчас незаконченное занятие."""
        return self.session is not None and not self.session.finished

    def current_word(self) -> Word | None:
        """Текущее слово или None, если занятия нет или оно закончено."""
        if self.session is None or self.session.finished:
            return None
        return self._vocabulary.get(self.session.current_key)

    # --- внутреннее ---------------------------------------------------------------

    def _begin(self, session: Session) -> None:
        self.session = session
        self._skip_missing_words()

    def _skip_missing_words(self) -> None:
        """Пропустить слова, которых больше нет в словаре, и сохранить место.

        Слово могли удалить из data/*.txt, пока занятие лежало сохранённым.
        Законченное занятие Settings.save_session не хранит: так оно пропадает
        из кнопки "Продолжить".
        """
        session = self.session
        while not session.finished and self._vocabulary.get(session.current_key) is None:
            session.skip_word()
        self._settings.save_session(session)
