# -*- coding: utf-8 -*-
"""Озвучка слов голосом Windows.

Что это в жизни: "запасной диктор", который всегда на месте. Живёт в
отдельном невидимом процессе PowerShell и читает фразы, которые ему
передают построчно. Интернет не нужен, ничего ставить не надо -
голос Microsoft Zira (en-US) уже есть в Windows.

Протокол общения с процессом: пишем строку - он её произносит.
"STOP" - замолчать. Конец ввода - процесс завершается сам.
"""

import base64
import subprocess
import threading

# Скрипт PowerShell: выбирает английский голос и читает строки из stdin.
_SPEAK_SCRIPT = r"""
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$v = $s.GetInstalledVoices() | Where-Object { $_.Enabled -and $_.VoiceInfo.Culture.Name -like 'en-*' } | Select-Object -First 1
if ($v) { $s.SelectVoice($v.VoiceInfo.Name); [Console]::Out.WriteLine('VOICE ' + $v.VoiceInfo.Name) }
else { [Console]::Out.WriteLine('NOVOICE') }
[Console]::Out.Flush()
while ($true) {
    $line = [Console]::In.ReadLine()
    if ($line -eq $null) { break }
    $s.SpeakAsyncCancelAll()
    if ($line -ne 'STOP') { [void]$s.SpeakAsync($line) }
}
"""


class Speaker:
    """Произносит английские слова. Безопасно вызывать из любого потока."""

    def __init__(self):
        self.voice: str | None = None
        self.ready = False
        self.error: str | None = None
        self._process: subprocess.Popen | None = None
        self._lock = threading.Lock()
        # Запуск PowerShell занимает около полсекунды - делаем в фоне.
        threading.Thread(target=self._start, daemon=True).start()

    def _start(self) -> None:
        # -EncodedCommand: скрипт в base64, так stdin свободен для фраз.
        encoded = base64.b64encode(_SPEAK_SCRIPT.encode("utf-16-le")).decode("ascii")
        try:
            self._process = subprocess.Popen(
                ["powershell", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
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

    def say(self, text: str) -> bool:
        """Произнести фразу. False - голос ещё не готов или сломался."""
        text = " ".join(text.split())  # без переводов строк
        if not text:
            return False
        with self._lock:
            if not self.ready or self._process is None or self._process.poll() is not None:
                return False
            try:
                self._process.stdin.write(text + "\n")
                self._process.stdin.flush()
                return True
            except OSError:
                self.ready = False
                return False

    def stop(self) -> None:
        """Замолчать немедленно."""
        if self.ready:
            with self._lock:
                try:
                    self._process.stdin.write("STOP\n")
                    self._process.stdin.flush()
                except OSError:
                    pass

    def close(self) -> None:
        """Закрыть диктора. После этого объект использовать нельзя."""
        if self._process and self._process.poll() is None:
            try:
                self._process.stdin.close()
                self._process.wait(timeout=0.5)
            except (OSError, subprocess.TimeoutExpired):
                self._process.kill()
                self._process.wait()

    def restart(self) -> None:
        """Перезапустить диктора, если он умер или не поднялся."""
        with self._lock:
            self.ready = False
            self.error = None
            old = self._process
            self._process = None
        if old and old.poll() is None:
            try:
                old.kill()
            except OSError:
                pass
        threading.Thread(target=self._start, daemon=True).start()
