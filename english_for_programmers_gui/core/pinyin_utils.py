# =============================================================================
# ОБЩИЕ УТИЛИТЫ ПИНЬИНЯ — слоги, разбиение, убирание тонов
# =============================================================================
#
# Этот модуль — единый источник правды для работы с пиньинем.
# Раньше списки слогов, разбиение на слоги и убирание тонов жили в двух
# местах (tests/unit/test_chinese_data.py и core/pinyin_ru.py), теперь здесь.
#
# Кто пользуется: проверка данных (test_chinese_data.py), русское чтение
# пиньиня (pinyin_ru.py), грамматика китайского (grammar_zh.py — через тест).
#
# strip_tones из core/answers.py остаётся отдельно: он убирает и ü (для
# проверки ввода), это другое поведение.

import unicodedata
from functools import lru_cache


# --- списки слогов путунхуа ------------------------------------------------

INITIALS = "b p m f d t n l g k h j q x zh ch sh r z c s".split()

SPECIAL = """a ai an ang ao e ei en eng er o ou
zhi chi shi ri zi ci si
ya yan yang yao ye yi yin ying yo yong you yu yuan yue yun
wa wai wan wang wei wen weng wo wu""".split()

FINALS = """a ai an ang ao e ei en eng o ong ou
i ia ian iang iao ie in ing iong iu
u ua uai uan uang ui un uo v ve van vn ue uan un""".split()

SYLLABLES = set(SPECIAL) | {i + f for i in INITIALS for f in FINALS}


# --- убирание тонов ------------------------------------------------

# Значки-тоны как combining marks (macron, acute, caron, grave).
# Диерезис над ü (U+0308) НЕ входит — его сохраняем.
_TONE_MARKS = {"\u0304", "\u0301", "\u030c", "\u0300"}


def bare(text: str) -> str:
    """Убрать тоны, ü превратить в v: "nǚ" -> "nv", "mā" -> "ma"."""
    parts = unicodedata.normalize("NFD", text)
    kept = "".join(ch for ch in parts if ch not in _TONE_MARKS)
    return unicodedata.normalize("NFC", kept).lower().replace("ü", "v")


# --- разбиение на слоги ------------------------------------------------

def best_split(b: str) -> list[str] | None:
    """Разбить слитный пиньинь (уже bare) на слоги-строки, или None.
    
    Используется pinyin_ru.py для русского чтения.
    """
    parts = _best_parts(b)
    return None if parts is None else [b[a:e] for a, e in parts]


def _best_parts(b: str) -> tuple | None:
    """Разбить слитный пиньинь (bare) на кортеж пар (начало, конец), или None.
    
    Внутренняя функция для split_syllables и best_split.
    """
    @lru_cache(None)
    def best(start: int) -> tuple | None:
        if start == len(b):
            return ()
        options = []
        for end in range(start + 1, min(start + 6, len(b)) + 1):
            rest = best(end)
            if b[start:end] in SYLLABLES and rest is not None:
                options.append(((start, end), *rest))
        return min(options, key=len) if options else None
    return best(0)


def split_syllables(word: str) -> list[str] | None:
    """Разбить слово пиньиня на слоги С ТОНАМИ: "diànnǎo" -> ["diàn", "nǎo"].
    
    Если не выходит — None. Буква r на конце (эризация) режется: "diǎnr" -> ["diǎn"].
    """
    toned = unicodedata.normalize("NFC", word).lower().replace("ü", "v")
    b = bare(word)
    if len(toned) != len(b):  # редкий случай необычной записи
        toned = b
    # эризация: r на конце — не отдельный слог
    if b.endswith("r") and _best_parts(b) is None and len(b) > 1:
        return split_syllables(word[:-1])
    parts = _best_parts(b)
    return None if parts is None else [toned[a:e] for a, e in parts]