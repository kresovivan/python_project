# -*- coding: utf-8 -*-
"""Тесты настроек питомца."""

import json
import tempfile
import unittest
from pathlib import Path

from core.settings import Settings, load, save


class TestSettings(unittest.TestCase):
    def test_defaults_when_no_file(self):
        """Без файла - настройки по умолчанию."""
        s = load(Path(tempfile.gettempdir()) / "no_such_settings.json")
        self.assertEqual(s, Settings())

    def test_save_and_load_roundtrip(self):
        """Сохранённое читается обратно без потерь."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            s = Settings(scale=1.0, sleep_after_idle=600, sound=False)
            save(path, s)
            self.assertEqual(load(path), s)

    def test_broken_file_gives_defaults(self):
        """Битый JSON не роняет программу - просто умолчания."""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "settings.json"
            p.write_text("{битый json", encoding="utf-8")
            self.assertEqual(load(p), Settings())

    def test_unknown_keys_ignored(self):
        """Лишние ключи из будущих версий игнорируются."""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "settings.json"
            p.write_text(json.dumps({"scale": 1.0, "будущее": 42}),
                         encoding="utf-8")
            s = load(p)
            self.assertEqual(s.scale, 1.0)
            self.assertFalse(hasattr(s, "будущее"))


class TestApplySettings(unittest.TestCase):
    def test_apply_changes_policy(self):
        """apply_settings переносит числа в политику поведения."""
        from gui.app import KisunchikApp
        ASSETS = Path(__file__).resolve().parent.parent / "assets"

        class FakeClock:
            now = 1000.0
            def __call__(self):
                return self.now

        s = Settings(sleep_after_idle=60, fun_every=20, walk_every=30)
        app = KisunchikApp(ASSETS, clock=FakeClock(), idle_probe=lambda: 0.0,
                           settings=s)
        try:
            self.assertEqual(app.policy.sleep_after_idle, 60)
            self.assertEqual(app.policy.fun_period, (12.0, 28.0))
            self.assertEqual(app.policy.walk_delay, (18.0, 42.0))
        finally:
            app.speaker.close()
            app.window.root.destroy()

    def test_change_settings_persists(self):
        """Изменение через меню сохраняется в файл."""
        from gui.app import KisunchikApp
        ASSETS = Path(__file__).resolve().parent.parent / "assets"

        class FakeClock:
            now = 1000.0
            def __call__(self):
                return self.now

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            app = KisunchikApp(ASSETS, clock=FakeClock(), idle_probe=lambda: 0.0,
                               settings=Settings(), settings_path=path)
            try:
                app.change_settings(sound=False, scale=0.5)
                on_disk = load(path)
                self.assertFalse(on_disk.sound)
                self.assertEqual(on_disk.scale, 0.5)
                # Размер котика применился сразу.
                self.assertEqual(app.window.cat_w, app.atlas.out_width)
            finally:
                app.speaker.close()
                app.window.root.destroy()


if __name__ == "__main__":
    unittest.main()
