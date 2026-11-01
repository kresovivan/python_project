import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from core import speech
from core.speech import DEFAULT_VOICE, SYSTEM, NeuralVoice, Speaker
from tests.support import close_process_stdout


class SpeechUnitTests(unittest.TestCase):
    def test_cache_path_depends_on_text_speed_and_voice(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(speech, "edge_tts", None):
            voice = NeuralVoice(Path(tmp), DEFAULT_VOICE)
            normal = voice.cache_path("browser cache", False)
            self.assertNotEqual(normal, voice.cache_path("browser cache", True))
            self.assertNotEqual(normal, voice.cache_path("another text", False))
            voice.voice = "en-GB-SoniaNeural"
            self.assertNotEqual(normal, voice.cache_path("browser cache", False))
            self.assertFalse(voice.available)
            self.assertFalse(voice.say("test"))
            voice.close()


@unittest.skipUnless(sys.platform == "win32", "Для проигрывания нужен Windows MCI")
@unittest.skipUnless(os.environ.get("EFP_AUDIO_TESTS") == "1", "Звук и сеть: задайте EFP_AUDIO_TESTS=1")
class RealSpeechTests(unittest.TestCase):
    def test_neural_cache_slow_voice_and_windows_fallback(self):
        with tempfile.TemporaryDirectory(prefix="efp_voice_test_") as tmp:
            speaker = Speaker(Path(tmp), DEFAULT_VOICE)
            try:
                deadline = time.monotonic() + 8
                while not speaker.system.ready and not speaker.system.error and time.monotonic() < deadline:
                    time.sleep(0.05)
                self.assertTrue(speaker.system.ready, speaker.system.error)

                text = "browser cache"
                self.assertFalse(speaker.neural.is_cached(text))
                self.assertTrue(speaker.say(text))
                self.assertIn("Загружаю", speaker.pop_message()[0])
                deadline = time.monotonic() + 60
                while time.monotonic() < deadline:
                    speaker.poll()
                    if speaker.neural.is_cached(text) and speaker.neural._want_play is None:
                        break
                    time.sleep(0.05)
                self.assertTrue(speaker.neural.is_cached(text), speaker.pop_message())
                path = speaker.neural.cache_path(speaker.neural.prepare(text), False)
                self.assertGreater(path.stat().st_size, 1000)
                self.assertTrue(speaker.neural.player._opened)
                speaker.stop()

                self.assertTrue(speaker.say(text))
                self.assertIsNone(speaker.pop_message())
                speaker.stop()

                prefetched = "prefetch test"
                speaker.prefetch(prefetched)
                speaker.prefetch(prefetched)
                deadline = time.monotonic() + 60
                while not speaker.neural.is_cached(prefetched) and time.monotonic() < deadline:
                    speaker.poll()
                    time.sleep(0.05)
                self.assertTrue(speaker.neural.is_cached(prefetched))
                self.assertIsNone(speaker.neural._want_play)

                self.assertTrue(speaker.say(text, slow=True))
                deadline = time.monotonic() + 60
                while time.monotonic() < deadline:
                    speaker.poll()
                    if speaker.neural.is_cached(text, True) and speaker.neural._want_play is None:
                        break
                    time.sleep(0.05)
                self.assertTrue(speaker.neural.is_cached(text, True))
                self.assertNotEqual(speaker.neural.cache_path(text, False), speaker.neural.cache_path(text, True))
                speaker.stop()

                speaker.set_voice(SYSTEM)
                self.assertFalse(speaker.uses_neural)
                self.assertTrue(speaker.say("Windows voice test"))
                speaker.stop()
                speaker.set_voice(DEFAULT_VOICE)
                speaker.neural.available = False
                self.assertTrue(speaker.say("Offline test"))
                speaker.stop()
            finally:
                process = speaker.system._process
                speaker.close()
                close_process_stdout(process)
                self.assertTrue(process is None or process.poll() is not None)


if __name__ == "__main__":
    unittest.main()
