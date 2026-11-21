# -*- coding: utf-8 -*-
"""Автозапуск питомца вместе с Windows.

Что это в жизни: "будильник системы". Windows при входе пользователя
смотрит в реестр и папку автозагрузки и запускает всё, что там лежит.

У нас три способа записаться, от простого к хитрому:
1. реестр напрямую (HKCU\\...\\Run);
2. реестр через reg.exe - помогает, когда антивирус запрещает
   свежесобранному exe писать в реестр самому (WinError 5);
3. ярлык в папке "Автозагрузка" - на случай, если реестр для нас
   закрыт совсем.
"""

import os
import subprocess
import sys
import winreg
from pathlib import Path

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "KisunchikPet"

def _ps_quote(value: str) -> str:
    """Экранировать строку для подстановки в PowerShell-скрипт."""
    return "'" + value.replace("'", "''") + "'"


def _lnk_create_script(link: Path, target: str, arguments: str) -> str:
    """Скрипт создания ярлыка со значениями, вшитыми в текст.

    Значения вставляем прямо в скрипт, а не через $args: powershell
    -Command склеивает аргументы обратно в строку, и путь с пробелами
    ("Start Menu") разваливается на куски.
    """
    workdir = str(Path(target).parent)
    return (
        "$ws = New-Object -ComObject WScript.Shell;"
        f"$s = $ws.CreateShortcut({_ps_quote(str(link))});"
        f"$s.TargetPath = {_ps_quote(target)};"
        f"$s.Arguments = {_ps_quote(arguments)};"
        f"$s.WorkingDirectory = {_ps_quote(workdir)};"
        "$s.Save()"
    )


def launch_target() -> tuple[str, str]:
    """Кого запускать и с какими аргументами.

    В собранном exe - просто он сам. Из исходников - pythonw с run.py,
    чтобы не висело чёрное окно консоли.
    """
    if getattr(sys, "frozen", False):
        return sys.executable, ""
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    run_py = Path(__file__).resolve().parent.parent / "run.py"
    return str(pythonw), f'"{run_py}"'


def launch_command() -> str:
    """Строка запуска для реестра: путь плюс аргументы."""
    target, arguments = launch_target()
    return f'"{target}" {arguments}'.strip()


def _startup_link() -> Path:
    """Ярлык в папке автозагрузки текущего пользователя."""
    return Path(os.environ.get("APPDATA", "")) / (
        r"Microsoft\Windows\Start Menu\Programs\Startup\Kisunchik.lnk")


def _open_key(writable: bool):
    """Открыть ветку автозапуска. В тестах подменяется заглушкой."""
    access = winreg.KEY_SET_VALUE if writable else winreg.KEY_READ
    return winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, access)


def _run(arguments: list[str]) -> None:
    """Запустить внешнюю команду без окна, ошибку вернуть как OSError."""
    try:
        subprocess.run(arguments, check=True, capture_output=True,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except subprocess.CalledProcessError as exc:
        # Консольные утилиты Windows ругаются в cp866.
        detail = (exc.stderr or b"").decode("cp866", errors="replace").strip()
        raise OSError(f"{arguments[0]}: код {exc.returncode} {detail}") from exc


def _registry_enable() -> None:
    """Записаться в реестр: сначала напрямую, потом через reg.exe."""
    try:
        with _open_key(writable=True) as key:
            winreg.SetValueEx(key, VALUE_NAME, 0, winreg.REG_SZ, launch_command())
    except OSError:
        _run(["reg", "add", f"HKCU\\{RUN_KEY}", "/v", VALUE_NAME,
              "/t", "REG_SZ", "/d", launch_command(), "/f"])


def _link_enable() -> None:
    """Положить ярлык в папку автозагрузки."""
    target, arguments = launch_target()
    script = _lnk_create_script(_startup_link(), target, arguments)
    _run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script])


def is_enabled() -> bool:
    """Записан ли котик в автозапуск прямо сейчас (любым способом)."""
    try:
        with _open_key(writable=False) as key:
            winreg.QueryValueEx(key, VALUE_NAME)
        return True
    except OSError:
        return _startup_link().exists()


def enable() -> None:
    """Добавить котика в автозапуск любым доступным способом."""
    try:
        _registry_enable()
    except OSError:
        _link_enable()


def disable() -> None:
    """Убрать котика из автозапуска. Отсутствие записи - не ошибка."""
    try:
        with _open_key(writable=True) as key:
            winreg.DeleteValue(key, VALUE_NAME)
    except OSError:
        try:
            _run(["reg", "delete", f"HKCU\\{RUN_KEY}", "/v", VALUE_NAME, "/f"])
        except OSError:
            pass
    try:
        _startup_link().unlink()
    except OSError:
        pass


def apply(turn_on: bool) -> None:
    """Привести автозапуск в соответствие с настройкой."""
    if turn_on:
        enable()
    else:
        disable()
