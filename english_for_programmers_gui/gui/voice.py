# =============================================================================
# УПРАВЛЕНИЕ ОЗВУЧКОЙ из интерфейса
# =============================================================================
#
# Speaker (core/speech.py) умеет говорить, но ничего не знает об окне.
# VoiceController связывает его с интерфейсом:
#   - помнит настройки (голос, "Произносить сразу");
#   - каждые 100 мс даёт Speaker обработать скачанные фразы;
#   - показывает сообщения Speaker во всплывающей подсказке Toast.
# Страницы пользуются только этим классом: say(), auto_say(), prefetch().

from core.settings import Settings
from core.speech import Speaker
from gui.toast import Toast


class VoiceController:
    POLL_MS = 100
    GREETING = "Hello! Let's learn English."  # звучит сразу после смены голоса

    def __init__(self, root, speaker: Speaker, settings: Settings, toast: Toast):
        self._root = root
        self._speaker = speaker
        self._settings = settings
        self._toast = toast
        self._root.after(self.POLL_MS, self._poll)

    # --- настройки ---------------------------------------------------------------

    @property
    def voice(self) -> str:
        """Код выбранного голоса, например "en-US-JennyNeural"."""
        return self._speaker.voice

    def set_voice(self, code: str) -> None:
        self._speaker.set_voice(code)
        self._settings.set("voice", code)
        self.say(self.GREETING)  # сразу даём послушать новый голос

    @property
    def auto_speak(self) -> bool:
        return bool(self._settings.get("auto_speak", False))

    @auto_speak.setter
    def auto_speak(self, enabled: bool) -> None:
        # @x.setter - метод вызывается при присваивании: voice.auto_speak = True
        self._settings.set("auto_speak", enabled)

    # --- произношение ---------------------------------------------------------------

    def say(self, text: str | None, slow: bool = False) -> None:
        self._speaker.say(text, slow=slow)
        self._show_message()

    def auto_say(self, text: str | None) -> None:
        """Произнести, только если включено "Произносить сразу"."""
        if self.auto_speak:
            self.say(text)

    def prefetch(self, text: str | None) -> None:
        """Заранее скачать произношение, чтобы по P оно прозвучало мгновенно."""
        self._speaker.prefetch(text)

    def close(self) -> None:
        self._speaker.close()

    # --- внутреннее -----------------------------------------------------------------

    def _poll(self) -> None:
        self._speaker.poll()
        self._show_message()
        self._root.after(self.POLL_MS, self._poll)

    def _show_message(self) -> None:
        message = self._speaker.pop_message()
        if message:
            text, kind = message
            self._toast.show(text, kind=kind)
