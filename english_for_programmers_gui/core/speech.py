# =============================================================================
# ОЗВУЧКА - произношение английских слов
# =============================================================================
#
# Два "движка" (engine) с одинаковым интерфейсом:
#
#   VoiceEngine (абстрактный)
#   |-- SystemVoice  - голос Windows (Zira). Без интернета, звучит "роботом".
#   `-- NeuralVoice  - нейросетевые голоса Microsoft Edge (Jenny, Andrew, ...)
#                      через библиотеку edge-tts. Звучат как живой человек.
#
#   Speaker - то, с чем работает программа. Выбирает движок по настройке,
#   а если нейросетевой голос недоступен (нет интернета) - говорит голосом Windows.
#
# Нейросетевой голос:
#   - слово скачивается ОДИН раз и сохраняется в user_data/audio/ (кэш),
#     повторно звучит мгновенно и без интернета;
#   - скачивание идёт в отдельном потоке, чтобы окно не "замирало";
#   - сервис иногда отвечает пустотой - делаем до 3 попыток.
#
# Важно про потоки: tkinter и проигрыватель Windows работают только в главном
# потоке. Поэтому фоновый поток лишь скачивает файл и кладёт результат в очередь
# (queue), а главный поток забирает его в методе Speaker.poll() и проигрывает.

import asyncio
import base64
import ctypes
import hashlib
import itertools
import queue
import re
import subprocess
import threading
import time
from abc import ABC, abstractmethod
from pathlib import Path

try:
    import edge_tts  # pip install edge-tts
except ImportError:  # библиотека не установлена - будет только голос Windows
    edge_tts = None

SYSTEM = "system"  # особое значение настройки "голос": голос Windows

# (код голоса, название в меню). Порядок = порядок в списке выбора.
VOICES = [
    ("en-US-JennyNeural", "Jenny (США, женский)"),
    ("en-US-AndrewNeural", "Andrew (США, мужской)"),
    ("en-US-AriaNeural", "Aria (США, женский)"),
    ("en-US-GuyNeural", "Guy (США, мужской)"),
    ("en-US-EmmaNeural", "Emma (США, женский)"),
    ("en-US-BrianNeural", "Brian (США, мужской)"),
    ("en-GB-SoniaNeural", "Sonia (Британия, женский)"),
    ("en-GB-RyanNeural", "Ryan (Британия, мужской)"),
    (SYSTEM, "Zira (Windows, без интернета)"),
]
DEFAULT_VOICE = "en-US-JennyNeural"


# =============================================================================
# Общий интерфейс движка
# =============================================================================


class VoiceEngine(ABC):
    """Общий интерфейс любого голоса.

    Что это в жизни: "должностная инструкция голоса". Любой голос обязан
    уметь say (произнести), stop (замолчать) и close (уйти домой). Speaker
    работает с любым голосом по этой инструкции и не знает, как тот устроен.
    """

    @staticmethod
    def prepare(text: str) -> str:
        """Подготовить текст для голоса.

        "commit (DB)" превращается в "commit" (пояснение в скобках не читаем)
        "UPDATE ... SET" превращается в "UPDATE SET"
        "NameError" превращается в "Name Error" (иначе голос читает слитно)
        "read_only" превращается в "read only"
        """
        text = re.sub(r"\(.*?\)", " ", text)
        text = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", text)
        text = text.replace("_", " ").replace("...", " ").replace("\u2026", " ").replace("\n", " ")
        return " ".join(text.split())

    @abstractmethod
    def say(self, text: str, slow: bool = False) -> bool:
        """Произнести (или начать готовить) текст. False - движок недоступен."""

    def stop(self) -> None:
        """Остановить текущую фразу."""

    def close(self) -> None:
        """Освободить ресурсы при выходе из программы."""


# =============================================================================
# Голос Windows (Zira) - через невидимый процесс PowerShell
# =============================================================================

# Скрипт PowerShell читает строки из stdin:
#   "RATE n" - скорость (от -10 до 10),  "STOP" - замолчать,  иначе - текст для произношения.
_SYSTEM_SCRIPT = r"""
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$v = $s.GetInstalledVoices() | Where-Object { $_.Enabled -and $_.VoiceInfo.Culture.Name -like 'en-*' } | Select-Object -First 1
if ($v) { $s.SelectVoice($v.VoiceInfo.Name); [Console]::Out.WriteLine('VOICE ' + $v.VoiceInfo.Name) }
else { [Console]::Out.WriteLine('NOVOICE') }
[Console]::Out.Flush()
while ($true) {
    $line = [Console]::In.ReadLine()
    if ($line -eq $null) { break }
    if ($line.StartsWith('RATE ')) { $s.Rate = [int]$line.Substring(5); continue }
    $s.SpeakAsyncCancelAll()
    if ($line -ne 'STOP') { [void]$s.SpeakAsync($line) }
}
"""


class SystemVoice(VoiceEngine):
    """Голос Windows (Zira): без интернета, звучит "роботом".

    Что это в жизни: "запасной диктор", который всегда на месте. Живёт в
    отдельном невидимом процессе PowerShell и читает фразы, которые ему
    передают построчно.
    """

    NORMAL_RATE = 0
    SLOW_RATE = -5

    def __init__(self):
        self.voice: str | None = None
        self.ready = False
        self.error: str | None = None
        self._rate = self.NORMAL_RATE
        self._process: subprocess.Popen | None = None
        # Запуск PowerShell занимает ~0.5 с - делаем в фоне, чтобы окно не ждало.
        threading.Thread(target=self._start, daemon=True).start()

    def _start(self) -> None:
        # -EncodedCommand: скрипт в base64, так stdin процесса свободен для наших фраз.
        encoded = base64.b64encode(_SYSTEM_SCRIPT.encode("utf-16-le")).decode("ascii")
        try:
            self._process = subprocess.Popen(
                ["powershell", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),  # без чёрного окна
            )
            first_line = self._process.stdout.readline().strip()
        except OSError as exc:
            self.error = f"не удалось запустить PowerShell: {exc}"
            return
        if first_line.startswith("VOICE "):
            self.voice = first_line[6:]
            self.ready = True
        else:
            self.error = "в Windows не установлен английский голос"

    def _send(self, line: str) -> bool:
        if not self.ready or self._process.poll() is not None:
            return False
        try:
            self._process.stdin.write(line + "\n")
            self._process.stdin.flush()
            return True
        except OSError:
            self.ready = False
            return False

    def say(self, text: str, slow: bool = False) -> bool:
        text = self.prepare(text)
        if not text:
            return False
        rate = self.SLOW_RATE if slow else self.NORMAL_RATE
        if rate != self._rate and self._send(f"RATE {rate}"):
            self._rate = rate
        return self._send(text)

    def stop(self) -> None:
        self._send("STOP")

    def close(self) -> None:
        if self._process and self._process.poll() is None:
            try:
                self._process.stdin.close()  # скрипт прочитает "конец ввода" и завершится
                self._process.wait(timeout=0.5)
            except (OSError, subprocess.TimeoutExpired):
                self._process.kill()  # ещё договаривает - останавливаем сразу
                self._process.wait()


# =============================================================================
# Проигрыватель MP3 - встроенный в Windows MCI (Media Control Interface)
# =============================================================================


class Mp3Player:
    """Проигрывает MP3 средствами Windows, без сторонних библиотек.

    Что это в жизни: "магнитофон". Ему дают файл - он его играет.

    ctypes позволяет вызвать функцию из системной библиотеки winmm.dll
    прямо из Python. Команды MCI - это обычные строки: "open ...", "play ...".
    Вызывать только из главного потока программы.
    """

    ALIAS = "efp_sound"

    def __init__(self):
        self._send = ctypes.windll.winmm.mciSendStringW
        self._opened = False

    def play(self, path: Path) -> bool:
        self.stop()
        if self._send(f'open "{path}" type mpegvideo alias {self.ALIAS}', None, 0, 0) != 0:
            return False
        self._opened = True
        return self._send(f"play {self.ALIAS}", None, 0, 0) == 0

    def stop(self) -> None:
        if self._opened:
            self._send(f"close {self.ALIAS}", None, 0, 0)
            self._opened = False


# =============================================================================
# Нейросетевые голоса Microsoft Edge (edge-tts) + кэш файлов
# =============================================================================


class NeuralVoice(VoiceEngine):
    """Нейросетевые голоса Microsoft Edge (Jenny, Andrew ...): звучат как живой человек.

    Что это в жизни: "диктор со студией звукозаписи". Каждую фразу он один
    раз записывает в файл (скачивает через интернет) и кладёт на полку
    (кэш user_data/audio/). Потом фраза звучит с полки мгновенно и без
    интернета. Записывает в фоне, а проигрывает магнитофон Mp3Player.
    """

    SLOW_RATE = "-35%"
    NORMAL_RATE = "+0%"
    ATTEMPTS = 3  # сервис иногда отвечает пустотой - пробуем ещё раз

    def __init__(self, cache_dir: Path, voice: str):
        self.cache_dir = cache_dir
        self.voice = voice
        self.available = edge_tts is not None
        self.player = Mp3Player()
        # Задания для фонового потока: (приоритет, номер, текст, голос, скорость, путь).
        # PriorityQueue отдаёт сначала задания с МЕНЬШИМ приоритетом:
        # 0 - "произнести сейчас", 1 - "скачать заранее".
        self._jobs: queue.PriorityQueue = queue.PriorityQueue()
        self._results: queue.Queue = queue.Queue()  # (путь, ошибка или None)
        self._counter = itertools.count()  # номер задания - для порядка при равном приоритете
        self._pending: set[Path] = set()  # файлы, которые сейчас скачиваются
        self._want_play: Path | None = None  # что нужно проиграть, как только скачается
        self._want_text: tuple[str, bool] | None = None  # тот же текст - для запасного голоса
        if self.available:
            threading.Thread(target=self._worker, daemon=True).start()

    # --- путь к файлу в кэше ------------------------------------------------------

    def cache_path(self, text: str, slow: bool) -> Path:
        rate = self.SLOW_RATE if slow else self.NORMAL_RATE
        # Имя файла - "отпечаток" (хеш) голоса, скорости и текста: у одинакового
        # текста всегда одинаковое имя, у разного - разное.
        digest = hashlib.sha1(f"{self.voice}|{rate}|{text}".encode()).hexdigest()[:20]
        return self.cache_dir / self.voice / f"{digest}.mp3"

    @staticmethod
    def _is_ready(path: Path) -> bool:
        return path.exists() and path.stat().st_size > 0

    # --- запросы из главного потока -------------------------------------------------

    def say(self, text: str, slow: bool = False) -> bool:
        """Проиграть сразу из кэша или поставить в очередь на скачивание."""
        if not self.available:
            return False
        text = self.prepare(text)
        if not text:
            return False
        path = self.cache_path(text, slow)
        self._want_play, self._want_text = None, None
        if self._is_ready(path):
            return self.player.play(path)
        self._want_play, self._want_text = path, (text, slow)
        self._enqueue(0, text, slow, path)
        return True

    def prefetch(self, text: str) -> None:
        """Скачать произношение заранее, ничего не проигрывая."""
        if not self.available:
            return
        text = self.prepare(text)
        if text:
            path = self.cache_path(text, False)
            if not self._is_ready(path):
                self._enqueue(1, text, False, path)

    def is_cached(self, text: str, slow: bool = False) -> bool:
        return self._is_ready(self.cache_path(self.prepare(text), slow))

    def _enqueue(self, priority: int, text: str, slow: bool, path: Path) -> None:
        if path in self._pending:
            return  # уже скачивается - дождёмся
        self._pending.add(path)
        rate = self.SLOW_RATE if slow else self.NORMAL_RATE
        self._jobs.put((priority, next(self._counter), text, self.voice, rate, path))

    def poll(self) -> tuple[bool, list[tuple[str, bool]]]:
        """Обработать то, что скачал фоновый поток (вызывать из главного потока).

        Проигрывает ожидаемую фразу, если она скачалась. Возвращает:
          - удалось ли что-то проиграть;
          - фразы (текст, медленно), которые скачать не удалось, - их
            скажет запасной голос.
        """
        played, failed = False, []
        while True:
            try:
                path, error = self._results.get_nowait()
            except queue.Empty:
                return played, failed
            self._pending.discard(path)
            if path != self._want_play:
                continue  # это была заготовка заранее или уже неактуальный запрос
            want = self._want_text
            self._want_play, self._want_text = None, None
            if error is None:
                played = self.player.play(path) or played
            elif want:
                failed.append(want)

    def stop(self) -> None:
        self._want_play, self._want_text = None, None
        self.player.stop()

    def close(self) -> None:
        self.player.stop()

    # --- фоновый поток ---------------------------------------------------------------

    def _worker(self) -> None:
        while True:
            _, _, text, voice, rate, path = self._jobs.get()
            error = None
            for attempt in range(self.ATTEMPTS):
                try:
                    self._download(text, voice, rate, path)
                    error = None
                    break
                # Ловим ЛЮБУЮ ошибку намеренно: это фоновый поток, и если ошибка
                # вылетит из него, он молча умрёт, и звук пропадёт до перезапуска.
                # Ошибка не теряется: её текст уходит в очередь результатов.
                except Exception as exc:  # noqa: BLE001 - сеть, пустой ответ сервиса и т. п.
                    error = f"{type(exc).__name__}: {exc}"
                    time.sleep(0.4 * (attempt + 1))
            self._results.put((path, error))

    @staticmethod
    def _download(text: str, voice: str, rate: str, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        # Сначала пишем во временный файл: при сбое edge-tts оставляет пустой
        # файл, и он не должен попасть в кэш как "готовый".
        tmp = path.with_suffix(".part")
        asyncio.run(edge_tts.Communicate(text, voice, rate=rate).save(str(tmp)))
        if tmp.stat().st_size == 0:
            tmp.unlink(missing_ok=True)
            raise RuntimeError("сервис вернул пустой звук")
        tmp.replace(path)


# =============================================================================
# Speaker - то, чем пользуется программа
# =============================================================================


class Speaker:
    """Выбирает голос по настройке и при сбое переключается на голос Windows.

    Что это в жизни: "диктор", у которого два голоса. Обычно он читает живым
    нейросетевым голосом, а если тот недоступен (нет интернета, нет
    библиотеки) - голосом Windows. Окно программы говорит диктору только
    "произнеси это", а какой голос выбрать, решает он сам.

    Сообщения для пользователя (например, 'нет интернета') копятся внутри,
    интерфейс забирает их методом pop_message() и показывает.
    """

    def __init__(
        self,
        cache_dir: Path,
        voice: str = DEFAULT_VOICE,
        *,
        system: VoiceEngine | None = None,
        neural: NeuralVoice | None = None,
    ):
        """cache_dir - папка для скачанных фраз; voice - выбранный голос.

        system и neural - сами голоса. Обычно их не передают, и Speaker
        создаёт настоящие. Тесты передают заглушки (tests/unit/test_speaker.py):
        так правило выбора голоса проверяется без звука и интернета.
        Звёздочка * в списке параметров значит: system и neural можно
        передать только по имени, Speaker(..., system=...), не по порядку.
        """
        self.system = system or SystemVoice()
        self.neural = neural or NeuralVoice(cache_dir, voice if voice != SYSTEM else DEFAULT_VOICE)
        self.voice = voice
        self._messages: list[tuple[str, str]] = []  # (текст, вид: "info" или "error")
        self._warned_offline = False

    @property
    def uses_neural(self) -> bool:
        return self.voice != SYSTEM and self.neural.available

    def set_voice(self, voice: str) -> None:
        self.stop()
        self.voice = voice
        if voice != SYSTEM:
            self.neural.voice = voice
            if not self.neural.available:
                self._messages.append(("Не установлена библиотека edge-tts: pip install edge-tts", "error"))

    def say(self, text: str | None, slow: bool = False) -> bool:
        if not text:
            return False
        self.stop()
        if self.uses_neural:
            cached = self.neural.is_cached(text, slow)
            if self.neural.say(text, slow):
                if not cached:
                    self._messages.append(("Загружаю произношение...", "info"))
                return True
        if self.system.say(text, slow):
            return True
        if self.system.error:
            self._messages.append((f"Озвучка недоступна: {self.system.error}", "error"))
        else:
            self._messages.append(("Голос ещё загружается, нажмите через секунду", "info"))
        return False

    def prefetch(self, text: str | None) -> None:
        if text and self.uses_neural:
            self.neural.prefetch(text)

    def pop_message(self) -> tuple[str, str] | None:
        """Самое свежее сообщение для пользователя (или None). Остальные отбрасываются."""
        if not self._messages:
            return None
        message = self._messages[-1]
        self._messages.clear()
        return message

    def poll(self) -> None:
        """Вызывается каждые 100 мс: проигрывает скачанное, при сбое говорит голосом Windows."""
        played, failed = self.neural.poll()
        if played:
            self._warned_offline = False  # связь есть - при следующем сбое снова предупредим
        for text, slow in failed:
            self.system.say(text, slow)
            if not self._warned_offline:
                self._warned_offline = True
                self._messages.append(
                    ("Нейросетевой голос недоступен (нет интернета?) - говорю голосом Windows", "error")
                )

    def stop(self) -> None:
        self.neural.stop()
        self.system.stop()

    def close(self) -> None:
        self.neural.close()
        self.system.close()
