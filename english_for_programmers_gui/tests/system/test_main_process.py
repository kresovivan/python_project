# Программа целиком: python main.py открывает окно и закрывается крестиком.
#
# Это единственный тест, который запускает программу так же, как вы:
# отдельным процессом. Он ловит ошибки, которые не видны тестам окна,
# например зависание при закрытии (было: "can't delete Tcl command").

import json
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from tests.support import (
    copy_resources,
    send_wm_close,
    titled_windows,
    wait_for_new_window,
)

# Сколько секунд ждать появления окна и его закрытия. Запас большой:
# первый запуск после сборки бывает медленным (файлы проверяет антивирус).
START_TIMEOUT = 30
CLOSE_TIMEOUT = 30


@unittest.skipUnless(
    sys.platform == "win32", "Окно закрывается сообщением Windows WM_CLOSE"
)
class MainProcessTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="efp_main_process_")
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        copy_resources(self.root)
        # Ошибки программы пишем в файл, а не в канал (pipe): переполненный
        # канал может заблокировать программу, и тест зависнет.
        self.stderr_path = self.root / "stderr.txt"

    def start_program(self) -> subprocess.Popen:
        previous = set(titled_windows())
        stderr = self.stderr_path.open("w", encoding="utf-8")
        self.addCleanup(stderr.close)
        process = subprocess.Popen(
            [sys.executable, "-X", "utf8", str(self.root / "main.py")],
            cwd=self.root,
            stdout=subprocess.DEVNULL,
            stderr=stderr,
        )
        self.addCleanup(self.stop_program, process)
        self.hwnd = wait_for_new_window(previous, process, START_TIMEOUT)
        return process

    def stop_program(self, process: subprocess.Popen) -> None:
        """Уборка после теста: закрыть программу, если тест её не закрыл.

        Сначала крестиком (WM_CLOSE), как пользователь: тогда программа сама
        завершит свой голос Windows (отдельный процесс PowerShell). Если сразу
        "убить" программу, PowerShell ещё какое-то время живёт и держит
        временную папку, и её не удаётся удалить.
        """
        if process.poll() is not None:
            return
        if self.hwnd:
            send_wm_close(self.hwnd)
        try:
            process.wait(timeout=CLOSE_TIMEOUT)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

    def close_window(self, process: subprocess.Popen) -> int:
        time.sleep(0.5)  # дать окну дорисоваться
        send_wm_close(self.hwnd)
        return process.wait(timeout=CLOSE_TIMEOUT)

    def test_window_opens(self):
        self.start_program()

        self.assertIsNotNone(self.hwnd, "Окно программы не появилось")

    def test_window_closes_without_errors(self):
        process = self.start_program()

        exit_code = self.close_window(process)

        self.assertEqual(exit_code, 0)
        self.assertEqual(self.stderr_path.read_text(encoding="utf-8").strip(), "")

    def test_window_position_is_saved_on_close(self):
        process = self.start_program()

        self.close_window(process)

        state = json.loads(
            (self.root / "user_data" / "state.json").read_text(encoding="utf-8")
        )
        self.assertTrue(state["window"]["geometry"])


if __name__ == "__main__":
    unittest.main()
