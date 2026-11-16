# =============================================================================
# АЗБУКА - английские буквы для тех, кто начинает с нуля
# =============================================================================
#
# Что это в жизни: "азбука с картинками", как у первоклассника. На каждой
# странице одна буква: большая и маленькая, как она называется, какой звук
# обычно даёт в словах, и слово с картинкой (чаще всего животное).
#
# Русские буквы в квадратных скобках - примерное звучание. Английских звуков,
# которых нет в русском, точно русскими буквами не записать, поэтому главное -
# послушать (клавиша P на странице "Азбука").
#
# Это данные, а не логика: список ALPHABET. Картинки - файлы в assets/alphabet/,
# рисунки проекта OpenMoji (openmoji.org), лицензия CC BY-SA 4.0.
# Кто пользуется: страница "Азбука" (gui/pages/alphabet.py).
# Тесты: tests/unit/test_alphabet.py.

from dataclasses import dataclass


@dataclass(frozen=True)
class Letter:
    """Одна страница азбуки."""

    upper: str  # большая буква: "A"
    name_ru: str  # как называется буква: "эй"
    sound_ru: str  # какой звук обычно даёт в словах: "[э] как в cat"
    word: str  # слово-пример: "Ant"
    word_sound: str  # как читается слово: "энт"
    word_ru: str  # перевод: "муравей"
    picture: str  # файл картинки в assets/alphabet/: "ant.png"

    @property
    def lower(self) -> str:
        """Маленькая буква: "a"."""
        return self.upper.lower()

    @property
    def speech(self) -> str:
        """Что произнести: буква, потом слово. Точки дают голосу паузу."""
        return f"{self.upper}. {self.word}."


ALPHABET: tuple[Letter, ...] = (
    Letter("A", "эй", "[э] как в cat, [эй] как в name", "Ant", "энт", "муравей", "ant.png"),
    Letter("B", "би", "[б]", "Bear", "бэа", "медведь", "bear.png"),
    Letter("C", "си", "[к], а перед e, i, y - [с]: cat, city", "Cat", "кэт", "кошка", "cat.png"),
    Letter("D", "ди", "[д]", "Dog", "дог", "собака", "dog.png"),
    Letter("E", "и", "[э] как в pen, [и] как в me", "Elephant", "элифэнт", "слон", "elephant.png"),
    Letter("F", "эф", "[ф]", "Frog", "фрог", "лягушка", "frog.png"),
    Letter("G", "джи", "[г], а перед e, i, y часто [дж]: go, giraffe", "Giraffe", "джираф", "жираф", "giraffe.png"),
    Letter("H", "эйч", "[х], лёгкий выдох, как будто греете руки", "Horse", "хорс", "лошадь", "horse.png"),
    Letter("I", "ай", "[и] как в it, [ай] как в like", "Iguana", "игуана", "игуана", "iguana.png"),
    Letter("J", "джей", "[дж]", "Jellyfish", "джелифиш", "медуза", "jellyfish.png"),
    Letter("K", "кей", "[к]", "Kangaroo", "кэнгару", "кенгуру", "kangaroo.png"),
    Letter("L", "эл", "[л]", "Lion", "лайэн", "лев", "lion.png"),
    Letter("M", "эм", "[м]", "Monkey", "манки", "обезьяна", "monkey.png"),
    Letter("N", "эн", "[н]", "Nest", "нэст", "гнездо", "nest.png"),
    Letter("O", "оу", "[о] как в dog, [оу] как в go", "Owl", "аул", "сова", "owl.png"),
    Letter("P", "пи", "[п]", "Penguin", "пэнгуин", "пингвин", "penguin.png"),
    Letter("Q", "кью", "почти всегда вместе с u: qu = [кв]", "Queen", "куин", "королева", "queen.png"),
    Letter("R", "ар", "[р], мягкий, язык не дрожит", "Rabbit", "рэбит", "кролик", "rabbit.png"),
    Letter("S", "эс", "[с], иногда [з]: is", "Snake", "снэйк", "змея", "snake.png"),
    Letter("T", "ти", "[т]", "Tiger", "тайгэ", "тигр", "tiger.png"),
    Letter("U", "ю", "[а] как в up, [ю] как в use", "Unicorn", "юникорн", "единорог", "unicorn.png"),
    Letter("V", "ви", "[в]", "Violin", "вайэлин", "скрипка", "violin.png"),
    Letter("W", "дабл-ю", "[у], губы трубочкой: [уэ] в we", "Wolf", "вулф", "волк", "wolf.png"),
    Letter("X", "экс", "[кс], чаще в конце слова", "Fox", "фокс", "лиса", "fox.png"),
    Letter("Y", "уай", "[й] в начале слова, [ай] или [и] в конце", "Yo-yo", "йоу-йоу", "йо-йо", "yoyo.png"),
    Letter("Z", "зи (в Британии зед)", "[з]", "Zebra", "зибра", "зебра", "zebra.png"),
)


def find_letter(char: str) -> Letter | None:
    """Найти страницу азбуки по символу ("c" или "C"). Не буква - None."""
    for letter in ALPHABET:
        if letter.upper == char.upper():
            return letter
    return None
