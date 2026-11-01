# Настоящий звук: нейросетевой голос edge-tts (интернет) и голос Windows.
#
# Во время теста будут слышны английские фразы. По умолчанию тест
# пропускается, запуск - с переменной окружения EFP_AUDIO_TESTS=1
# (см. tests/README.md). Кэш звука - во временной папке, ваш не трогается.

import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

from core.speech import DEFAULT_VOICE, SYSTEM, Speaker

DOWNLOAD_TIMEOUT = 60  # секунд на скачивание одной фразы


@unittest.skipUnless(sys.platform == "win32", "Для проигрывания нужен Windows MCI")
@unittest.skipUnless(
    os.environ.get("EFP_AUDIO_TESTS") == "1", "Звук и сеть: задайте EFP_AUDIO_TESTS=1"
)
class RealSpeechTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="efp_voice_test_")
        self.addCleanup(tmp.cleanup)
        self.speaker = Speaker(Path(tmp.name), DEFAULT_VOICE)
        self.addCleanup(self.close_speaker)
        self.wait_for_system_voice()

    def close_speaker(self) -> None:
        self.speaker.close()
        # Голос Windows - отдельный процесс PowerShell. close() его завершает,
        # но канал вывода остаётся открытым, и Python пишет ResourceWarning.
        # Закрываем канал сами: это внутренняя деталь, но только для уборки.
        process = self.speaker.system._process
        if process and process.stdout:
            process.stdout.close()

    def wait_for_system_voice(self) -> None:
        deadline = time.monotonic() + 8
        while (
            not (self.speaker.system.ready or self.speaker.system.error)
            and time.monotonic() < deadline
        ):
            time.sleep(0.05)

    def wait_for_download(self, text: str, slow: bool = False) -> bool:
        """Ждать, пока фраза скачается. Возвращает: проигралась ли она за это время."""
        played = False
        deadline = time.monotonic() + DOWNLOAD_TIMEOUT
        cached_at = None
        while time.monotonic() < deadline:
            done, _ = self.speaker.neural.poll()
            played = played or done
            if cached_at is None and self.speaker.neural.is_cached(text, slow):
                cached_at = time.monotonic()
            # Файл появился - ещё полсекунды забираем результаты фонового
            # потока: сообщение "скачано, можно играть" приходит чуть позже файла.
            if cached_at is not None and time.monotonic() - cached_at > 0.5:
                break
            time.sleep(0.05)
        time.sleep(1.5)  # дать фразе дозвучать
        return played

    def test_windows_voice_starts(self):
        self.assertTrue(self.speaker.system.ready, self.speaker.system.error)

    def test_new_phrase_is_downloaded_and_played(self):
        played_at_once = self.speaker.say("browser cache")
        message = self.speaker.pop_message()

        played = self.wait_for_download("browser cache")

        self.assertTrue(played_at_once)
        self.assertIn("Загружаю", message[0])
        self.assertTrue(self.speaker.neural.is_cached("browser cache"))
        self.assertTrue(played)

    def test_cached_phrase_plays_without_loading_message(self):
        self.speaker.say("browser cache")
        self.wait_for_download("browser cache")
        self.speaker.pop_message()

        self.speaker.say("browser cache")

        self.assertIsNone(self.speaker.pop_message())

    def test_slow_phrase_is_cached_separately(self):
        self.speaker.say("browser cache", slow=True)

        self.wait_for_download("browser cache", slow=True)

        self.assertTrue(self.speaker.neural.is_cached("browser cache", slow=True))
        self.assertFalse(self.speaker.neural.is_cached("browser cache", slow=False))

    def test_prefetch_downloads_without_playing(self):
        self.speaker.prefetch("prefetch test")

        played = self.wait_for_download("prefetch test")

        self.assertTrue(self.speaker.neural.is_cached("prefetch test"))
        self.assertFalse(played)

    def test_windows_voice_speaks_when_chosen(self):
        self.speaker.set_voice(SYSTEM)

        spoken = self.speaker.say("Windows voice test")
        time.sleep(1.5)

        self.assertFalse(self.speaker.uses_neural)
        self.assertTrue(spoken)

    def test_windows_voice_replaces_unavailable_neural_voice(self):
        self.speaker.neural.available = False

        spoken = self.speaker.say("Offline test")
        time.sleep(1.5)

        self.assertTrue(spoken)


if __name__ == "__main__":
    unittest.main()
