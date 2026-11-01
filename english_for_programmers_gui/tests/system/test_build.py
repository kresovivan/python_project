# Сборка exe (build_exe.py) во временной копии проекта.
#
# Медленно (около минуты) и нужен PyInstaller, поэтому по умолчанию тест
# пропускается. Запуск: задать переменную окружения EFP_BUILD_TESTS=1
# (как именно - в tests/README.md). Ваша папка dist/ и ярлык не меняются.

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from tests.support import (
    DATA,
    copy_resources,
    send_wm_close,
    titled_windows,
    wait_for_new_window,
)


@unittest.skipUnless(sys.platform == "win32", "Проверка exe предназначена для Windows")
@unittest.skipUnless(
    os.environ.get("EFP_BUILD_TESTS") == "1",
    "Медленная сборка: задайте EFP_BUILD_TESTS=1",
)
class BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Собираем ОДИН раз на все тесты класса: сборка - самая долгая часть,
        # а тесты только читают её результат.
        cls._tmp = tempfile.TemporaryDirectory(prefix="efp_build_test_")
        root = Path(cls._tmp.name) / "english_for_programmers_gui"
        copy_resources(root)
        cls.result = subprocess.run(
            [sys.executable, "build_exe.py", "--no-shortcut"],
            check=False,  # ошибку сборки не бросаем, а проверяем в тесте ниже
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,
        )
        cls.exe = root / "dist" / "EnglishForProgrammers" / "EnglishForProgrammers.exe"
        cls.internal = cls.exe.parent / "_internal"

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_build_finishes_without_errors(self):
        self.assertEqual(self.result.returncode, 0, self.result.stderr[-4000:])

    def test_exe_file_is_created(self):
        self.assertTrue(self.exe.exists())

    def test_all_dictionary_files_are_inside(self):
        packed = sorted(path.name for path in (self.internal / "data").glob("*.txt"))

        self.assertEqual(packed, sorted(path.name for path in DATA.glob("*.txt")))

    def test_icon_is_inside(self):
        self.assertTrue((self.internal / "assets" / "icon.ico").exists())

    def test_exe_opens_and_closes_and_saves_window(self):
        previous = set(titled_windows())
        process = subprocess.Popen([str(self.exe)], cwd=self.exe.parent)
        try:
            hwnd = wait_for_new_window(previous, process, timeout=35)
            self.assertIsNotNone(hwnd, "Окно exe не появилось")
            time.sleep(0.5)

            send_wm_close(hwnd)

            self.assertEqual(process.wait(timeout=30), 0)
            state = json.loads(
                (self.exe.parent / "user_data" / "state.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertTrue(state["window"]["geometry"])
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()


if __name__ == "__main__":
    unittest.main()
