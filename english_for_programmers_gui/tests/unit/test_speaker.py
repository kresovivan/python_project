# Выбор голоса (core/speech.py, класс Speaker) - без звука и интернета.
#
# Speaker получает оба голоса снаружи (system=..., neural=...). Программа
# передаёт настоящие, а тест - заглушки, которые ничего не произносят,
# только записывают, что их попросили сказать. Так проверяется само
# правило выбора голоса и переход на голос Windows при сбое.

import unittest
from pathlib import Path

from core.speech import SYSTEM, Speaker


class FakeNeuralVoice:
    """Заглушка нейросетевого голоса (вместо NeuralVoice)."""

    def __init__(self):
        self.available = True  # библиотека edge-tts "установлена"
        self.voice = "en-US-JennyNeural"
        self.cached: set[tuple[str, bool]] = set()  # какие фразы "уже скачаны"
        self.said: list[tuple[str, bool]] = []
        self.prefetched: list[str] = []
        self.poll_result: tuple[bool, list] = (False, [])  # что вернёт следующий poll()

    def is_cached(self, text, slow=False):
        return (text, slow) in self.cached

    def say(self, text, slow=False):
        if not self.available:
            return False
        self.said.append((text, slow))
        return True

    def prefetch(self, text):
        self.prefetched.append(text)

    def poll(self):
        return self.poll_result

    def stop(self): ...

    def close(self): ...


class FakeSystemVoice:
    """Заглушка голоса Windows (вместо SystemVoice)."""

    def __init__(self):
        self.ready = True
        self.error: str | None = None
        self.said: list[tuple[str, bool]] = []

    def say(self, text, slow=False):
        if not self.ready:
            return False
        self.said.append((text, slow))
        return True

    def stop(self): ...

    def close(self): ...


class SpeakerTestCase(unittest.TestCase):
    def setUp(self):
        self.neural = FakeNeuralVoice()
        self.system = FakeSystemVoice()
        self.speaker = self.make_speaker()

    def make_speaker(self, voice: str = "en-US-JennyNeural") -> Speaker:
        return Speaker(Path("unused"), voice, system=self.system, neural=self.neural)

    def message(self) -> str:
        """Текст сообщения для пользователя (или пустая строка, если сообщения нет)."""
        message = self.speaker.pop_message()
        return message[0] if message else ""


class ChooseVoiceTests(SpeakerTestCase):
    def test_neural_voice_speaks_when_available(self):
        self.speaker.say("loop")

        self.assertEqual(self.neural.said, [("loop", False)])
        self.assertEqual(self.system.said, [])

    def test_windows_voice_speaks_when_chosen(self):
        self.speaker.set_voice(SYSTEM)

        self.speaker.say("loop")

        self.assertEqual(self.system.said, [("loop", False)])

    def test_windows_voice_replaces_neural_voice_without_library(self):
        self.neural.available = False

        self.speaker.say("loop")

        self.assertEqual(self.system.said, [("loop", False)])

    def test_slow_speech_is_passed_to_voice(self):
        self.speaker.say("loop", slow=True)

        self.assertEqual(self.neural.said, [("loop", True)])

    def test_empty_text_is_not_spoken(self):
        self.assertFalse(self.speaker.say(""))
        self.assertEqual((self.neural.said, self.system.said), ([], []))

    def test_new_voice_is_given_to_neural_engine(self):
        self.speaker.set_voice("en-GB-SoniaNeural")

        self.assertEqual(self.neural.voice, "en-GB-SoniaNeural")


class MessagesTests(SpeakerTestCase):
    """Сообщения для пользователя: окно показывает их всплывающей подсказкой."""

    def test_new_phrase_shows_loading_message(self):
        self.speaker.say("loop")

        self.assertIn("Загружаю", self.message())

    def test_downloaded_phrase_plays_without_message(self):
        self.neural.cached.add(("loop", False))

        self.speaker.say("loop")

        self.assertEqual(self.message(), "")

    def test_choosing_neural_voice_without_library_explains_what_to_install(self):
        self.neural.available = False

        self.speaker.set_voice("en-GB-SoniaNeural")

        self.assertIn("edge-tts", self.message())

    def test_broken_windows_voice_is_reported(self):
        self.neural.available = False
        self.system.ready = False
        self.system.error = "в Windows не установлен английский голос"

        self.speaker.say("loop")

        self.assertIn("Озвучка недоступна", self.message())

    def test_only_latest_message_is_shown(self):
        self.speaker.say("loop")
        self.speaker.say("break")

        self.message()

        self.assertEqual(self.message(), "")


class OfflineTests(SpeakerTestCase):
    """Нет интернета: фраза не скачалась - её говорит голос Windows."""

    def test_failed_phrase_is_spoken_by_windows_voice(self):
        self.neural.poll_result = (False, [("loop", True)])

        self.speaker.poll()

        self.assertEqual(self.system.said, [("loop", True)])

    def test_user_is_warned_about_missing_internet(self):
        self.neural.poll_result = (False, [("loop", False)])

        self.speaker.poll()

        self.assertIn("нет интернета", self.message())

    def test_warning_is_shown_once_while_internet_is_missing(self):
        self.neural.poll_result = (False, [("loop", False)])
        self.speaker.poll()
        self.message()

        self.speaker.poll()

        self.assertEqual(self.message(), "")

    def test_warning_is_shown_again_after_internet_came_back_and_was_lost(self):
        self.neural.poll_result = (False, [("loop", False)])
        self.speaker.poll()
        self.message()
        self.neural.poll_result = (True, [])  # фраза скачалась и проиграна
        self.speaker.poll()

        self.neural.poll_result = (False, [("break", False)])
        self.speaker.poll()

        self.assertIn("нет интернета", self.message())


class PrefetchTests(SpeakerTestCase):
    def test_phrase_is_downloaded_in_advance_for_neural_voice(self):
        self.speaker.prefetch("loop")

        self.assertEqual(self.neural.prefetched, ["loop"])

    def test_nothing_is_downloaded_for_windows_voice(self):
        self.speaker.set_voice(SYSTEM)

        self.speaker.prefetch("loop")

        self.assertEqual(self.neural.prefetched, [])


if __name__ == "__main__":
    unittest.main()
