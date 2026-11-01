import ctypes
import tempfile
import time
from pathlib import Path

from core.speech import DEFAULT_VOICE, NeuralVoice
from core.vocabulary import Vocabulary
from tests.support import DATA


def run():
    vocabulary = Vocabulary.from_folder(DATA)
    english_words = ["variable", "loop", "function", "commit", "debug", "browser cache"]
    words = [vocabulary.get(text) for text in english_words]
    if not all(words):
        raise RuntimeError("Одно из выбранных слов отсутствует в словаре")
    with tempfile.TemporaryDirectory(prefix="efp_listen_") as tmp:
        voice = NeuralVoice(Path(tmp), DEFAULT_VOICE)
        try:
            if not voice.available:
                raise RuntimeError("Библиотека edge-tts недоступна")
            for number, word in enumerate(words, 1):
                text = word.answer
                print(f"{number}. {text} - {word.ru}", flush=True)
                cached = voice.is_cached(text)
                if not voice.say(text):
                    raise RuntimeError(f"Не удалось запустить озвучку: {text}")
                if not cached:
                    deadline = time.monotonic() + 60
                    while time.monotonic() < deadline:
                        played, failed = voice.poll()
                        if played:
                            break
                        if failed:
                            raise RuntimeError(f"Ошибка озвучки {text}: {failed}")
                        time.sleep(0.05)
                    else:
                        raise TimeoutError(f"Сервис не ответил для слова: {text}")
                buffer = ctypes.create_unicode_buffer(256)
                result = voice.player._send(f"status {voice.player.ALIAS} length", buffer, 256, 0)
                if result != 0 or not buffer.value.isdigit():
                    raise RuntimeError(f"Не удалось узнать длительность звука: {text}")
                time.sleep(int(buffer.value) / 1000 + 0.45)
        finally:
            voice.close()


if __name__ == "__main__":
    run()
