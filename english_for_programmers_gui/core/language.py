# =============================================================================
# ЯЗЫК - всё, чем английский отличается от китайского, в одном объекте
# =============================================================================
#
# Что это в жизни: "комплект учебников по одному языку". В комплекте:
# словарь (папка со словами), дикторы (голоса), правило проверки диктанта,
# тетрадь с грамматикой и, у китайского, тетрадь "Звуки и тоны".
# Программа одна и та же, меняется только комплект: переключили язык -
# выдали другой комплект, а страницы работают с ним одинаково.
#
# Так устроены и сами упражнения: страница "Написание слова" не знает,
# какой язык учат. Она спрашивает у языка его проверяющего (checker) и
# пользуется им. Это и есть полиморфизм: один вызов checker.is_correct(),
# а правило у английского и китайского разное.
#
# Кто пользуется: окно App (gui/app.py) выбирает язык и собирает под него
# словарь, прогресс и страницы. Тесты: tests/unit/test_language.py.

from dataclasses import dataclass
from pathlib import Path

from core import grammar, grammar_zh, pinyin
from core.answers import AnswerChecker, PinyinChecker
from core.grammar import GrammarTopic
from core.speech import VOICES


@dataclass(frozen=True)
class Language:
    code: str  # короткий код: "en" или "zh"
    name: str  # название на самом языке, на переключателе: "English", "中文"
    name_ru: str  # по-русски, в сообщениях: "английский", "китайский"
    data_folder: str  # где слова, относительно папки программы: "data" или "data/zh"
    user_folder: str  # где прогресс, относительно user_data: "" - прямо в ней
    voices: tuple[tuple[str, str], ...]  # (код голоса, название в меню)
    default_voice: str
    greeting: str  # звучит после смены голоса
    checker: type[AnswerChecker]  # кто проверяет "Написание слова"
    typing_task: str  # что делать на странице "Написание слова"
    typing_label: str  # подпись над переводом в "Написании слова"
    typing_placeholder: str  # серая подсказка в пустом поле ввода
    search_examples: str  # что можно искать на странице "Словарь"
    grammar: tuple[GrammarTopic, ...]  # темы страницы "Грамматика"
    sounds: tuple[GrammarTopic, ...] = ()  # "Звуки и тоны"; пусто - английская азбука

    def data_dir(self, base_dir: Path) -> Path:
        return base_dir / self.data_folder

    def user_dir(self, user_data: Path) -> Path:
        return user_data / self.user_folder if self.user_folder else user_data

    @property
    def searches_sound(self) -> bool:
        """Искать ли слово по произношению. Да - если произношение латиницей (пиньинь)."""
        return self.checker is PinyinChecker


ENGLISH = Language(
    code="en",
    name="English",
    name_ru="английский",
    data_folder="data",
    # Английский - первый язык программы: его прогресс и настройки
    # всегда лежали прямо в user_data/. Оставляем там, чтобы ничего не потерять.
    user_folder="",
    voices=tuple(VOICES),
    default_voice="en-US-JennyNeural",
    greeting="Hello! Let's learn English.",
    checker=AnswerChecker,
    typing_task="Напишите английское слово по переводу. Регистр и знаки препинания не важны.",
    typing_label="КАК ПО-АНГЛИЙСКИ",
    typing_placeholder="введите слово...",
    search_examples="Например: loop, commit, refactor, кортеж, переменная.",
    grammar=grammar.TOPICS,
)

CHINESE = Language(
    code="zh",
    name="中文",
    name_ru="китайский",
    data_folder="data/zh",
    user_folder="zh",
    # Голоса Microsoft Edge для путунхуа (общепринятого китайского языка).
    # Голоса Windows для китайского обычно не установлены, поэтому его в списке нет.
    voices=(
        ("zh-CN-XiaoxiaoNeural", "Сяосяо (женский)"),
        ("zh-CN-YunxiNeural", "Юньси (мужской)"),
        ("zh-CN-XiaoyiNeural", "Сяои (женский)"),
        ("zh-CN-YunjianNeural", "Юньцзянь (мужской)"),
        ("zh-CN-YunyangNeural", "Юньян (мужской, диктор)"),
    ),
    default_voice="zh-CN-XiaoxiaoNeural",
    greeting="你好！我们学习中文吧。",
    checker=PinyinChecker,
    typing_task="Напишите пиньинь по переводу, тоны не нужны: 电脑 - diannao. Вместо ü пишите v.",
    typing_label="КАК ПО-КИТАЙСКИ (ПИНЬИНЬ)",
    typing_placeholder="введите пиньинь...",
    search_examples="Например: 电脑, diannao (пиньинь без тонов), ошибка, файл.",
    grammar=grammar_zh.TOPICS,
    sounds=pinyin.TOPICS,
)

LANGUAGES: dict[str, Language] = {language.code: language for language in (ENGLISH, CHINESE)}


def find_language(code: str | None) -> Language:
    """Язык по коду. Неизвестный код (или None) - английский."""
    return LANGUAGES.get(code, ENGLISH)
