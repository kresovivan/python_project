# =============================================================================
# РУССКОЕ ЧТЕНИЕ ПИНЬИНЯ - как китайское слово произнести русскому человеку
# =============================================================================
#
# Китайские слова записаны пиньинем - латиницей с тонами: "nǐ hǎo".
# Русскому человеку не всегда понятно, как это прочитать. Этот модуль
# превращает пиньинь в примерное русское чтение: "ни хао".
#
# Чтение ПРИМЕРНОЕ, оно помогает "на глаз" понять звучание и запомнить слово.
# Настоящее произношение даёт только голос программы (по щелчку).
#
# Как устроено:
#   1. пиньинь чистится (тоны убираются, ü становится v);
#   2. слово разбивается на слоги (даже если написано слитно: "diànnǎo");
#   3. каждый слог переводится в русские буквы по таблицам начальных
#      звуков (инициалей) и конечных частей (финалей).
#
# Списки инициалей/финалей - те же, что в проверке данных (tests/unit/
# test_chinese_data.py): они описывают настоящие слоги путунхуа.
#
# Кто пользуется: страницы словаря и упражнений показывают русское чтение
# рядом с пиньинем. Тесты: tests/unit/test_pinyin_ru.py.

import unicodedata

# Значки тонов (macron, acute, caron, grave) - их убираем. Диерезис (две точки
# над ü) НЕ трогаем: ü читается как "юй" и не должно путаться с u ("у").
_TONE_MARKS = {"\u0304", "\u0301", "\u030c", "\u0300"}


def _bare(text: str) -> str:
    """Убрать тоны, но сохранить ü (превратив в v). "nǚ" -> "nv", "mā" -> "ma"."""
    parts = unicodedata.normalize("NFD", text)
    kept = "".join(ch for ch in parts if ch not in _TONE_MARKS)
    return unicodedata.normalize("NFC", kept).lower().replace("ü", "v")


# --- разбиение на слоги -----------------------------------------------------
# Списки настоящих слогов путунхуа: начальные звуки, особые слоги без начала
# и конечные части. ü записано как v (та же договорённость, что в пиньине).

_INITIALS = "b p m f d t n l g k h j q x zh ch sh r z c s".split()

_SPECIAL = """a ai an ang ao e ei en eng er o ou
zhi chi shi ri zi ci si
ya yan yang yao ye yi yin ying yo yong you yu yuan yue yun
wa wai wan wang wei wen weng wo wu""".split()

_FINALS = """a ai an ang ao e ei en eng o ong ou
i ia ian iang iao ie in ing iong iu
u ua uai uan uang ui un uo v ve van vn ue uan un""".split()

_SYLLABLES = set(_SPECIAL) | {i + f for i in _INITIALS for f in _FINALS}


def _best_split(bare: str) -> list[str] | None:
    """Разбить слитный пиньинь (без тонов) на слоги, или None если не выходит.

    Ищем разбиение на наименьшее число слогов: "xian" - один слог, а не xi+an.
    Рекурсия с запоминанием (lru_cache) перебирает позиции и оставляет
    самый короткий набор.
    """
    from functools import lru_cache

    @lru_cache(None)
    def best(start: int) -> tuple | None:
        if start == len(bare):
            return ()
        options = []
        for end in range(start + 1, min(start + 6, len(bare)) + 1):
            rest = best(end)
            if bare[start:end] in _SYLLABLES and rest is not None:
                options.append(((start, end), *rest))
        return min(options, key=len) if options else None

    parts = best(0)
    return None if parts is None else [bare[a:b] for a, b in parts]


def _split_word(bare: str) -> tuple[list[str], bool]:
    """Разбить одно слово (без пробелов) на слоги.

    Возвращает (слоги, эризация). Эризация - буква r на конце после слога:
    "diǎnr" (点儿) читается "дяньр", r - не отдельный слог, а "р" в конце.
    """
    parts = _best_split(bare)
    if parts is not None:
        return parts, False
    if bare.endswith("r") and len(bare) > 1:
        inner = _best_split(bare[:-1])
        if inner is not None:
            return inner, True
    return [bare], False  # не разобрали - оставляем как есть


# --- перевод слога в русские буквы ------------------------------------------

_INITIAL_RU = {
    "b": "б", "p": "п", "m": "м", "f": "ф",
    "d": "д", "t": "т", "n": "н", "l": "л",
    "g": "г", "k": "к", "h": "х",
    "j": "цз", "q": "ц", "x": "с",
    "zh": "чж", "ch": "ч", "sh": "ш", "r": "ж",
    "z": "цз", "c": "ц", "s": "с",
}

_FINAL_RU = {
    "a": "а", "o": "о", "e": "э", "i": "и", "u": "у", "v": "юй",
    "ai": "ай", "ei": "эй", "ao": "ао", "ou": "оу",
    "an": "ань", "en": "энь", "ang": "ан", "eng": "эн", "ong": "ун",
    "ia": "я", "ie": "е", "iao": "яо", "iu": "ю", "ian": "янь",
    "in": "инь", "iang": "ян", "ing": "ин", "iong": "юн",
    "ua": "уа", "uo": "уо", "uai": "уай", "ui": "уэй",
    "uan": "уань", "un": "унь", "uang": "уан", "ueng": "уэн",
    "ve": "юэ", "van": "юань", "vn": "юнь",
}

# После j, q, x буква u на самом деле ü: ju = "цзю", а не "цзу".
_U_AFTER_JQX = {"u": "ю", "uan": "юань", "un": "юнь", "ue": "юэ"}

# Слоги с особым чтением: гласная почти не слышна.
_REDUCED_RU = {
    "zhi": "чжы", "chi": "чы", "shi": "шы", "ri": "жы",
    "zi": "цзы", "ci": "цы", "si": "сы",
}

# Слоги, которые начинаются с y или w: это гласные, записанные по правилам.
_Y_RU = {
    "yi": "и", "ya": "я", "ye": "е", "yao": "яо", "you": "ю",
    "yan": "янь", "yin": "инь", "yang": "ян", "ying": "ин",
    "yong": "юн", "yu": "юй", "yue": "юэ", "yuan": "юань", "yun": "юнь",
    "yo": "ё",
}

_W_RU = {
    "wu": "у", "wa": "уа", "wo": "уо", "wai": "уай", "wei": "уэй",
    "wan": "уань", "wen": "уэнь", "wang": "уан", "weng": "уэн",
}

# Гласные без начального звука (и без y/w).
_VOWEL_RU = {
    "a": "а", "o": "о", "e": "э", "ai": "ай", "ei": "эй",
    "ao": "ао", "ou": "оу", "an": "ань", "en": "энь",
    "ang": "ан", "eng": "эн", "er": "эр",
}


def _syllable_ru(syllable: str) -> str:
    """Русское чтение одного слога (без тонов, ü уже заменено на v)."""
    if syllable in _REDUCED_RU:
        return _REDUCED_RU[syllable]
    if syllable in _Y_RU:
        return _Y_RU[syllable]
    if syllable in _W_RU:
        return _W_RU[syllable]
    if syllable in _VOWEL_RU:
        return _VOWEL_RU[syllable]
    for initial in sorted(_INITIAL_RU, key=len, reverse=True):
        if syllable.startswith(initial):
            final = syllable[len(initial):]
            if initial in ("j", "q", "x") and final in _U_AFTER_JQX:
                return _INITIAL_RU[initial] + _U_AFTER_JQX[final]
            if final in _FINAL_RU:
                return _INITIAL_RU[initial] + _FINAL_RU[final]
    return syllable  # не разобрали - возвращаем как было


def russian_reading(pinyin: str) -> str:
    """Примерное русское чтение пиньиня: "nǐ hǎo" -> "ни хао".

    Слова могут быть слитными ("diànnǎo") или через пробел ("nǐ hǎo").
    Результат - слоги через пробел.
    """
    bare = _bare(pinyin).replace("'", "").replace("’", "")
    result: list[str] = []
    for chunk in bare.split():
        if not chunk:
            continue
        syllables, erhua = _split_word(chunk)
        for i, syllable in enumerate(syllables):
            reading = _syllable_ru(syllable)
            if erhua and i == len(syllables) - 1:
                reading += "р"
            result.append(reading)
    return " ".join(result)
