# Озвучка (core/speech.py): подготовка текста и имена файлов в кэше.
# Здесь нет сети и звука. Настоящий звук проверяет tests/system/test_real_speech.py.

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core import speech
from core.speech import DEFAULT_VOICE, NeuralVoice, VoiceEngine


class PrepareTextTests(unittest.TestCase):
    """Текст перед озвучкой: голос должен читать слова, а не значки."""

    def test_note_in_brackets_is_not_read(self):
        self.assertEqual(VoiceEngine.prepare("commit (DB)"), "commit")

    def test_joined_words_are_split(self):
        """Слово "NameError" голос читает слитно, а "Name Error" - как два слова."""
        self.assertEqual(VoiceEngine.prepare("NameError"), "Name Error")

    def test_underscore_is_read_as_space(self):
        self.assertEqual(VoiceEngine.prepare("read_only"), "read only")

    def test_ellipsis_is_not_read(self):
        self.assertEqual(VoiceEngine.prepare("UPDATE ... SET"), "UPDATE SET")


class CachePathTests(unittest.TestCase):
    """Имя файла в кэше: одинаковый запрос - тот же файл, другой запрос - другой."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="efp_speech_")
        self.addCleanup(tmp.cleanup)
        # edge_tts = None - как будто библиотека не установлена: фоновый
        # поток скачивания не запускается, в сеть никто не ходит.
        patcher = patch.object(speech, "edge_tts", None)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.voice = NeuralVoice(Path(tmp.name), DEFAULT_VOICE)
        self.addCleanup(self.voice.close)

    def test_same_request_gives_same_file(self):
        self.assertEqual(
            self.voice.cache_path("loop", False), self.voice.cache_path("loop", False)
        )

    def test_different_text_gives_different_file(self):
        self.assertNotEqual(
            self.voice.cache_path("loop", False), self.voice.cache_path("break", False)
        )

    def test_slow_speech_gives_different_file(self):
        self.assertNotEqual(
            self.voice.cache_path("loop", False), self.voice.cache_path("loop", True)
        )

    def test_different_voice_gives_different_file(self):
        jenny = self.voice.cache_path("loop", False)

        self.voice.voice = "en-GB-SoniaNeural"

        self.assertNotEqual(self.voice.cache_path("loop", False), jenny)


class MissingLibraryTests(unittest.TestCase):
    def test_neural_voice_without_edge_tts_is_unavailable(self):
        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.object(speech, "edge_tts", None),
        ):
            voice = NeuralVoice(Path(tmp), DEFAULT_VOICE)
            try:
                self.assertFalse(voice.available)
                self.assertFalse(voice.say("loop"))
            finally:
                voice.close()


if __name__ == "__main__":
    unittest.main()
