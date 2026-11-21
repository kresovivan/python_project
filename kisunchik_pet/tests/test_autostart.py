# -*- coding: utf-8 -*-
"""Тесты автозапуска: реестр подменяется словарём, настоящий не трогаем."""

import tempfile
import unittest
from pathlib import Path

from core import autostart
from core.settings import Settings, load


class FakeKey:
    """Поддельная ветка реестра: хранит значения в словаре."""

    def __init__(self, store):
        self.store = store

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def make_fake_winreg(store):
    """Собрать замену winreg, которая работает со словарём."""
    class FakeWinreg:
        HKEY_CURRENT_USER = "HKCU"
        KEY_SET_VALUE = 1
        KEY_READ = 2
        REG_SZ = 1

        @staticmethod
        def OpenKey(root, path, reserved, access):
            return FakeKey(store)

        @staticmethod
        def SetValueEx(key, name, reserved, kind, value):
            key.store[name] = value

        @staticmethod
        def QueryValueEx(key, name):
            if name not in key.store:
                raise OSError("нет такой записи")
            return key.store[name], 1

        @staticmethod
        def DeleteValue(key, name):
            if name not in key.store:
                raise OSError("нет такой записи")
            del key.store[name]

    return FakeWinreg


class TestAutostart(unittest.TestCase):
    def setUp(self):
        # Подменяем winreg внутри модуля на время теста.
        self.store = {}
        self._real_winreg = autostart.winreg
        autostart.winreg = make_fake_winreg(self.store)

    def tearDown(self):
        autostart.winreg = self._real_winreg

    def test_enable_writes_command(self):
        autostart.enable()
        self.assertIn(autostart.VALUE_NAME, self.store)
        self.assertIn("run.py", self.store[autostart.VALUE_NAME])

    def test_is_enabled_reflects_store(self):
        self.assertFalse(autostart.is_enabled())
        autostart.enable()
        self.assertTrue(autostart.is_enabled())

    def test_disable_removes_entry(self):
        autostart.enable()
        autostart.disable()
        self.assertFalse(autostart.is_enabled())

    def test_disable_without_entry_is_silent(self):
        # Записи нет - отключение не должно падать.
        autostart.disable()

    def test_apply_switches_both_ways(self):
        autostart.apply(True)
        self.assertTrue(autostart.is_enabled())
        autostart.apply(False)
        self.assertFalse(autostart.is_enabled())

    def test_reg_exe_fallback(self):
        """Если антивирус запретил прямую запись - идём через reg.exe."""
        class AngryWinreg:
            HKEY_CURRENT_USER = "HKCU"
            KEY_SET_VALUE = 1
            KEY_READ = 2
            REG_SZ = 1

            @staticmethod
            def OpenKey(*args):
                raise OSError(5, "Отказано в доступе")

        autostart.winreg = AngryWinreg
        calls = []
        real_run = autostart.subprocess.run
        autostart.subprocess.run = lambda cmd, **kw: calls.append(cmd)
        try:
            autostart.enable()
        finally:
            autostart.subprocess.run = real_run
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][:2], ["reg", "add"])
        self.assertIn(autostart.VALUE_NAME, calls[0])

    def test_link_fallback_when_registry_fully_blocked(self):
        """Если реестр закрыт совсем - кладём ярлык в автозагрузку."""
        class AngryWinreg:
            HKEY_CURRENT_USER = "HKCU"
            KEY_SET_VALUE = 1
            KEY_READ = 2
            REG_SZ = 1

            @staticmethod
            def OpenKey(*args):
                raise OSError(5, "Отказано в доступе")

        autostart.winreg = AngryWinreg
        calls = []
        real_run = autostart.subprocess.run

        def fake_run(cmd, **kw):
            calls.append(cmd)
            if cmd[0] == "reg":
                raise OSError("антивирус запретил")

        autostart.subprocess.run = fake_run
        try:
            autostart.enable()
        finally:
            autostart.subprocess.run = real_run
        kinds = [c[0] for c in calls]
        self.assertIn("reg", kinds, "не попробовали reg.exe")
        self.assertIn("powershell", kinds, "не попробовали ярлык")

    def test_is_enabled_sees_startup_link(self):
        """is_enabled видит ярлык в автозагрузке, даже без записи реестра."""
        with tempfile.TemporaryDirectory() as tmp:
            link = Path(tmp) / "Kisunchik.lnk"
            real_link = autostart._startup_link
            autostart._startup_link = lambda: link
            try:
                self.assertFalse(autostart.is_enabled())
                link.write_bytes(b"lnk")
                self.assertTrue(autostart.is_enabled())
            finally:
                autostart._startup_link = real_link


class TestAutostartSetting(unittest.TestCase):
    def test_default_is_on(self):
        """По умолчанию автозапуск включён."""
        self.assertTrue(Settings().autostart)

    def test_autostart_survives_save_load(self):
        """Настройка автозапуска переживает сохранение."""
        with tempfile.TemporaryDirectory() as tmp:
            from core.settings import save
            path = Path(tmp) / "settings.json"
            save(path, Settings(autostart=False))
            self.assertFalse(load(path).autostart)

    def test_change_settings_calls_sync(self):
        """Выключение галочки в меню вызывает синхронизацию реестра."""
        from gui.app import KisunchikApp
        ASSETS = Path(__file__).resolve().parent.parent / "assets"

        class FakeClock:
            now = 1000.0
            def __call__(self):
                return self.now

        calls = []
        app = KisunchikApp(ASSETS, clock=FakeClock(), idle_probe=lambda: 0.0,
                           settings=Settings(),
                           autostart_sync=lambda on: calls.append(on))
        try:
            calls.clear()
            app.change_settings(autostart=False)
            self.assertEqual(calls, [False])
            app.change_settings(autostart=True)
            self.assertEqual(calls, [False, True])
        finally:
            app.speaker.close()
            app.window.root.destroy()

    def test_blocked_sync_rolls_back_setting(self):
        """Если антивирус запретил запись - галочка честно откатывается."""
        from gui.app import KisunchikApp
        ASSETS = Path(__file__).resolve().parent.parent / "assets"

        class FakeClock:
            now = 1000.0
            def __call__(self):
                return self.now

        def broken_sync(on):
            raise OSError(5, "антивирус запретил")

        app = KisunchikApp(ASSETS, clock=FakeClock(), idle_probe=lambda: 0.0,
                           settings=Settings(autostart=True),
                           autostart_sync=broken_sync,
                           autostart_check=lambda: True)  # по факту включён
        try:
            # Просим выключить - не получилось, настройка возвращается.
            app.change_settings(autostart=False)
            self.assertTrue(app.settings.autostart,
                            "галочка соврала: выключено в меню, включено в системе")
        finally:
            app.speaker.close()
            app.window.root.destroy()


if __name__ == "__main__":
    unittest.main()
