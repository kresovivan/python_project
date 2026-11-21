# -*- coding: utf-8 -*-
"""Озвучка слов голосом Windows (SAPI прямо из процесса).

Что это в жизни: "диктор в соседней комнате". Раньше котик звонил
диктору по телефону (порождал PowerShell), но антивирус не пускал
звонок - слова доходили, а голос рождался мёртвым. Теперь диктор
сидит прямо внутри программы: говорим через Windows SAPI (SpVoice)
по COM, без дочерних процессов вообще.

Речь идёт в отдельном потоке, чтобы котик не замирал на время фразы.
Слова складываются в очередь и произносятся по одному.

Английский голос выбираем через SSML-тег <voice required="Language=409">:
не привязываемся к имени (Zira и т.п.), подойдёт любой en-US голос.
"""

import ctypes
import queue
import threading
from ctypes import wintypes
from xml.sax.saxutils import escape

# Маркер версии движка: по нему в журнале видно, какой код зашит в exe.
ENGINE = "sapi-inproc-1"

_CLSID_SPVOICE = "{96749377-3391-11D2-9EE3-00C04F797396}"
_IID_ISPVOICE = "{6C44DF74-72B9-4992-A1EC-EF996E0422D4}"
_CLSCTX_ALL = 0x17
_SVSF_IS_XML = 8
_SPEAK_VTABLE_INDEX = 20  # IUnknown 3 + ISpNotifySource 7 + ISpEventSource 3 + 7


def _guid(text: str) -> ctypes.Array:
    """Строка вида {....} в бинарный GUID."""
    buf = ctypes.create_string_buffer(16)
    hr = ctypes.windll.ole32.CLSIDFromString(text, buf)
    if hr != 0:
        raise OSError(f"CLSIDFromString: {hr:#x}")
    return buf


class _Voice:
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
        """Произнести синхронно. Вернёт HRESULT (0 - успех)."""
        return self._speak(self._ptr, text, flags, None)

    def release(self) -> None:
        if self._ptr:
            self._release(self._ptr)
            self._ptr = None


class Speaker:
    """Произносит английские слова. Безопасно вызывать из любого потока."""

    def __init__(self):
        self.voice: str | None = None
        self.ready = False
        self.error: str | None = None
        self.said_count = 0                 # сколько фраз реально произнесено
        self.speech_error: str | None = None  # последняя ошибка синтеза
        self._words: queue.Queue = queue.Queue()
        self._thread: threading.Thread | None = None
        self._start()

    # --- поток диктора ---

    def _start(self) -> None:
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def _worker(self) -> None:
        """Цикл диктора: создать голос и произносить слова из очереди."""
        ole32 = ctypes.windll.ole32
        ole32.CoInitialize(None)
        voice = None
        try:
            voice = _Voice()
            self.voice = "SAPI SpVoice"
            self.ready = True
            while True:
                text = self._words.get()
                if text is None:  # команда на завершение
                    break
                xml = f'<voice required="Language=409">{escape(text)}</voice>'
                hr = voice.speak(xml)
                if hr == 0:
                    self.said_count += 1
                    self.speech_error = None
                else:
                    # Нет английского голоса или SSML не понравился -
                    # произносим как есть, голосом по умолчанию.
                    hr = voice.speak(text, flags=0)
                    if hr == 0:
                        self.said_count += 1
                        self.speech_error = "нет en-US голоса, читаю голосом по умолчанию"
                    else:
                        self.speech_error = f"Speak: {hr & 0xFFFFFFFF:#x}"
        except OSError as exc:
            self.error = str(exc)
        finally:
            if voice is not None:
                voice.release()
            ole32.CoUninitialize()
            self.ready = False

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
