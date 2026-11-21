# -*- coding: utf-8 -*-
"""Озвучка слов: офлайн-голоса Windows и онлайн-голоса из интернета.

Что это в жизни: два диктора на подхвате.
1. Офлайн: Windows SAPI (SpVoice) прямо в процессе, без дочерних
   программ - антивирусу нечего перехватывать. Один установленный голос
   разнообразим темпом и высотой: медленно, быстро, низко, высоко.
2. Онлайн: Google Translate TTS - бесплатно и без ключа, зато с
   акцентами: американский, британский, австралийский, индийский.
   Мелодия скачивается в mp3 и играется через winmm (есть в любой
   Windows). Нет интернета - сами переключаемся на офлайн.

Речь идёт в отдельном потоке, котик не замирает. Слова складываются
в очередь и произносятся по одному. Счётчик said_count растёт после
каждой реально произнесённой фразы - по нему видно, что звук был.
"""

import ctypes
import queue
import tempfile
import threading
import urllib.parse
import urllib.request
import winreg
from ctypes import wintypes
from pathlib import Path
from xml.sax.saxutils import escape

# Маркер версии движка: по нему в журнале видно, какой код зашит в exe.
ENGINE = "hybrid-2"

_CLSID_SPVOICE = "{96749377-3391-11D2-9EE3-00C04F797396}"
_IID_ISPVOICE = "{6C44DF74-72B9-4992-A1EC-EF996E0422D4}"
_CLSCTX_ALL = 0x17
_SVSF_IS_XML = 8
_SPEAK_VTABLE_INDEX = 20  # IUnknown 3 + ISpNotifySource 7 + ISpEventSource 3 + 7

# Персонажи офлайн-голоса: id, название в меню, темп, высота.
PERSONAS = [
    ("sapi:auto", "Зира - как есть", 0, 0),
    ("sapi:slow", "Зира - медленно и чётко", -2, 0),
    ("sapi:fast", "Зира - быстрая речь", 2, 0),
    ("sapi:low", "Зира - низкий голос", 0, -3),
    ("sapi:high", "Зира - высокий голос", 0, 3),
]

# Онлайн-голоса: id - это домен Google, от него зависит акцент.
ONLINE_VOICES = [
    ("gtts:com", "Онлайн - американский акцент", "com"),
    ("gtts:co.uk", "Онлайн - британский акцент", "co.uk"),
    ("gtts:com.au", "Онлайн - австралийский акцент", "com.au"),
    ("gtts:co.in", "Онлайн - индийский акцент", "co.in"),
]

_TTS_URL = "https://translate.google.{tld}/translate_tts?ie=UTF-8&client=tw-ob&tl=en&q="
_USER_AGENT = {"User-Agent": "Mozilla/5.0"}


def _guid(text: str) -> ctypes.Array:
    """Строка вида {....} в бинарный GUID."""
    buf = ctypes.create_string_buffer(16)
    hr = ctypes.windll.ole32.CLSIDFromString(text, buf)
    if hr != 0:
        raise OSError(f"CLSIDFromString: {hr:#x}")
    return buf


def installed_voices() -> list[dict]:
    """Голоса SAPI из реестра: имя для SSML и красивая подпись.

    Читаем реестр напрямую - это работает даже там, где COM не поднять.
    """
    found = []
    root = r"SOFTWARE\Microsoft\Speech\Voices\Tokens"
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, root)
    except OSError:
        return found
    i = 0
    while True:
        try:
            token = winreg.EnumKey(key, i)
        except OSError:
            break
        i += 1
        try:
            sub = winreg.OpenKey(key, token)
            display = winreg.QueryValueEx(sub, "")[0]
        except OSError:
            continue
        short = display.split(" - ")[0].strip()
        found.append({"id": token, "name": short, "label": display})
    return found


def voice_choices() -> list[tuple[str, str]]:
    """Все варианты голоса для меню: (id для настроек, подпись)."""
    choices = [(spec, label) for spec, label, _rate, _pitch in PERSONAS]
    for token in installed_voices():
        if token["name"] != "Microsoft Zira Desktop":  # Зира уже есть в персонажах
            choices.append((f"sapi:{token['name']}", token["label"]))
    choices += [(spec, label) for spec, label, _tld in ONLINE_VOICES]
    return choices


class _SapiVoice:
    """COM-объект SpVoice и его метод Speak. Живёт в одном потоке."""

    def __init__(self):
        ole32 = ctypes.windll.ole32
        self._ptr = ctypes.c_void_p()
        hr = ole32.CoCreateInstance(_guid(_CLSID_SPVOICE), None, _CLSCTX_ALL,
                                    _guid(_IID_ISPVOICE), ctypes.byref(self._ptr))
        if hr != 0:
            raise OSError(f"CoCreateInstance(SpVoice): {hr:#x}")
        vtbl_holder = ctypes.cast(self._ptr, ctypes.POINTER(ctypes.c_void_p)).contents
        vtable = ctypes.cast(vtbl_holder, ctypes.POINTER(ctypes.c_void_p * 40)).contents
        self._speak = ctypes.WINFUNCTYPE(
            ctypes.c_long, ctypes.c_void_p, wintypes.LPCWSTR,
            wintypes.DWORD, ctypes.c_void_p)(vtable[_SPEAK_VTABLE_INDEX])
        self._release = ctypes.WINFUNCTYPE(
            ctypes.c_ulong, ctypes.c_void_p)(vtable[2])

    def speak(self, text: str, flags: int = _SVSF_IS_XML) -> int:
        return self._speak(self._ptr, text, flags, None)

    def release(self) -> None:
        if self._ptr:
            self._release(self._ptr)
            self._ptr = None


def _ssml(text: str, name: str | None, rate: int, pitch: int) -> str:
    """Собрать SSML: голос по имени или языку, темп и высота."""
    inner = escape(text)
    if pitch:
        inner = f'<pitch absmiddle="{pitch:+d}">{inner}</pitch>'
    if rate:
        inner = f'<rate absspeed="{rate:+d}">{inner}</rate>'
    required = f"Name={name}" if name else "Language=409"
    return f'<voice required="{required}">{inner}</voice>'


def _play_mp3(path: str) -> None:
    """Проиграть mp3 через winmm MCI и подождать конца."""
    mci = ctypes.windll.winmm.mciSendStringW
    buf = ctypes.create_unicode_buffer(256)
    alias = f"tts{id(path) & 0xFFFF}"
    if mci(f'open "{path}" type mpegvideo alias {alias}', buf, 256, 0) != 0:
        raise OSError(f"mci open: {buf.value}")
    try:
        if mci(f"play {alias} wait", buf, 256, 0) != 0:
            raise OSError(f"mci play: {buf.value}")
    finally:
        mci(f"close {alias}", buf, 256, 0)


class Speaker:
    """Произносит английские слова. Безопасно вызывать из любого потока."""

    def __init__(self, voice_spec: str = "sapi:auto"):
        self.voice: str | None = None
        self.ready = False
        self.error: str | None = None
        self.said_count = 0                   # сколько фраз реально произнесено
        self.speech_error: str | None = None  # последняя ошибка синтеза
        self._voice_spec = voice_spec
        self._words: queue.Queue = queue.Queue()
        self._thread: threading.Thread | None = None
        self._start()

    # --- выбор голоса ---

    def set_voice(self, spec: str) -> None:
        """Поменять голос: sapi:auto, sapi:slow, gtts:co.uk и т.п."""
        self._voice_spec = spec

    # --- поток диктора ---

    def _start(self) -> None:
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def _worker(self) -> None:
        ole32 = ctypes.windll.ole32
        ole32.CoInitialize(None)
        sapi = None
        try:
            sapi = _SapiVoice()
            self.voice = "SAPI + онлайн"
            self.ready = True
            while True:
                text = self._words.get()
                if text is None:  # команда на завершение
                    break
                try:
                    self._say_one(sapi, text)
                except Exception as exc:  # одна фраза не должна убивать поток
                    self.speech_error = str(exc)
        except OSError as exc:
            self.error = str(exc)
        finally:
            if sapi is not None:
                sapi.release()
            ole32.CoUninitialize()
            self.ready = False

    def _say_one(self, sapi: _SapiVoice, text: str) -> None:
        """Произнести одну фразу текущим голосом."""
        spec = self._voice_spec
        if spec.startswith("gtts:"):
            tld = spec[5:]
            try:
                self._say_online(text, tld)
                return
            except OSError as exc:
                # Нет сети или Google ответил ошибкой - честно говорим
                # офлайн-голосом и пишем, почему.
                self.speech_error = f"онлайн недоступен ({exc}), говорю офлайн"
        # Офлайн: персонаж или конкретный установленный голос.
        rate = pitch = 0
        name = None
        for persona, _label, r, p in PERSONAS:
            if persona == spec:
                rate, pitch = r, p
                break
        else:
            if spec.startswith("sapi:") and spec != "sapi:auto":
                name = spec[5:]
        hr = sapi.speak(_ssml(text, name, rate, pitch))
        if hr == 0:
            self.said_count += 1
            if self.speech_error and "онлайн" not in self.speech_error:
                self.speech_error = None
        else:
            hr = sapi.speak(text, flags=0)
            if hr == 0:
                self.said_count += 1
            else:
                self.speech_error = f"Speak: {hr & 0xFFFFFFFF:#x}"

    def _say_online(self, text: str, tld: str) -> None:
        """Скачать озвучку у Google и проиграть через winmm."""
        url = _TTS_URL.format(tld=tld) + urllib.parse.quote(text)
        req = urllib.request.Request(url, headers=_USER_AGENT)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read()
        if len(data) < 100:
            raise OSError("пустой ответ Google TTS")
        path = Path(tempfile.gettempdir()) / f"kisunchik_tts_{self.said_count}.mp3"
        try:
            path.write_bytes(data)
            _play_mp3(str(path))
        finally:
            try:
                path.unlink()
            except OSError:
                pass
        self.said_count += 1
        self.speech_error = None

    # --- наружу ---

    def say(self, text: str) -> bool:
        """Поставить фразу в очередь на произнесение."""
        text = " ".join(text.split())  # без переводов строк
        if not text:
            return False
        if not self.ready:
            return False
        self._words.put(text)
        return True

    def stop(self) -> None:
        """Выбросить ещё не произнесённые слова из очереди."""
        while True:
            try:
                self._words.get_nowait()
            except queue.Empty:
                return

    def close(self) -> None:
        """Закрыть диктора. После этого объект использовать нельзя."""
        if self.ready:
            self._words.put(None)
        if self._thread is not None:
            self._thread.join(timeout=2)

    def restart(self) -> None:
        """Перезапустить диктора, если он умер или не поднялся."""
        self.close()
        self.ready = False
        self.error = None
        self._start()
