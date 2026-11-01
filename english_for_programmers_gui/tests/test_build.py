import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from tests.support import copy_resources, send_wm_close, titled_windows, wait_for_new_window


@unittest.skipUnless(sys.platform == "win32", "Проверка exe предназначена для Windows")
@unittest.skipUnless(os.environ.get("EFP_BUILD_TESTS") == "1", "Медленная сборка: задайте EFP_BUILD_TESTS=1")
class BuildTests(unittest.TestCase):
    def test_build_launch_save_and_close_exe(self):
        with tempfile.TemporaryDirectory(prefix="efp_build_test_") as tmp:
            root = Path(tmp) / "english_for_programmers_gui"
            copy_resources(root)
            result = subprocess.run(
                [sys.executable, "build_exe.py", "--no-shortcut"],
                cwd=root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=240,
            )
            self.assertEqual(result.returncode, 0, (result.stdout[-12000:], result.stderr[-12000:]))
            exe = root / "dist" / "EnglishForProgrammers" / "EnglishForProgrammers.exe"
            self.assertTrue(exe.exists())
            internal = exe.parent / "_internal"
            self.assertEqual(len(list((internal / "data").glob("*.txt"))), 18)
            self.assertTrue((internal / "assets" / "icon.ico").exists())

            previous = set(titled_windows())
            process = subprocess.Popen([str(exe)], cwd=exe.parent)
            try:
                hwnd = wait_for_new_window(previous, process, timeout=35)
                time.sleep(0.5)
                send_wm_close(hwnd)
                process.wait(timeout=12)
                self.assertEqual(process.returncode, 0)
                state_path = exe.parent / "user_data" / "state.json"
                self.assertTrue(state_path.exists())
                state = json.loads(state_path.read_text(encoding="utf-8"))
                self.assertTrue(state.get("window", {}).get("geometry"))
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()


if __name__ == "__main__":
    unittest.main()
