# Испорченные файлы прогресса и настроек: окно открывается и предупреждает.
#
# Как именно сохраняется копия испорченного файла, проверяют быстрые тесты
# tests/unit/test_storage.py. Здесь проверяется, что пользователь об этом узнаёт.

import unittest

from tests.gui.base import GuiTestCase


class BrokenProgressTests(GuiTestCase):
    def prepare_user_data(self):
        self.user_data.mkdir(parents=True)
        (self.user_data / "progress.json").write_text("{bad json", encoding="utf-8")

    def test_window_opens_on_home_page(self):
        self.assertEqual(self.app.current.key, "home")

    def test_user_is_told_where_broken_file_is_kept(self):
        message = self.app.toast.cget("text")

        self.assertIn("повреждён", message)
        self.assertIn("progress.broken-", message)


class BrokenSettingsTests(GuiTestCase):
    def prepare_user_data(self):
        self.user_data.mkdir(parents=True)
        (self.user_data / "state.json").write_text("{bad json", encoding="utf-8")

    def test_user_is_told_where_broken_file_is_kept(self):
        self.assertIn("state.broken-", self.app.toast.cget("text"))


class GoodFilesTests(GuiTestCase):
    def test_no_warning_when_files_are_fine(self):
        self.assertNotIn("повреждён", self.app.toast.cget("text"))


if __name__ == "__main__":
    unittest.main()
