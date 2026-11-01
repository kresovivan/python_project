# Файл с данными на диске (core/storage.py, класс JsonStore).
#
# Главное требование: прогресс пользователя нельзя потерять. Ни сбой во
# время записи, ни испорченный файл не должны молча стереть данные.

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.storage import JsonStore


class JsonStoreTestCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="efp_storage_")
        self.addCleanup(tmp.cleanup)
        self.folder = Path(tmp.name)
        self.path = self.folder / "progress.json"

    def files_in_folder(self) -> list[str]:
        return sorted(path.name for path in self.folder.iterdir())


class LoadTests(JsonStoreTestCase):
    def test_missing_file_gives_empty_data(self):
        self.assertEqual(JsonStore(self.path).load(), {})

    def test_saved_data_is_loaded_back(self):
        JsonStore(self.path).save({"words": {"loop": {"right": 3}}})

        self.assertEqual(JsonStore(self.path).load(), {"words": {"loop": {"right": 3}}})

    def test_russian_text_is_saved_as_is(self):
        """Файл можно открыть в блокноте и прочитать: без кодов вида \\u0446."""
        JsonStore(self.path).save({"topic": "Циклы"})

        self.assertIn("Циклы", self.path.read_text(encoding="utf-8"))


class SafeWriteTests(JsonStoreTestCase):
    def test_save_leaves_no_temporary_files(self):
        JsonStore(self.path).save({"a": 1})

        self.assertEqual(self.files_in_folder(), ["progress.json"])

    def test_failed_save_keeps_previous_data(self):
        """Сбой посреди записи (например, выключили компьютер) не портит старый файл.

        Сбой изображаем так: подмена файла (os.replace) - последний шаг
        записи - выбрасывает ошибку.
        """
        store = JsonStore(self.path)
        store.save({"version": "old"})

        with (
            patch("core.storage.os.replace", side_effect=OSError("сбой диска")),
            self.assertRaises(OSError),
        ):
            store.save({"version": "new"})

        self.assertEqual(JsonStore(self.path).load(), {"version": "old"})

    def test_folder_is_created_when_missing(self):
        path = self.folder / "user_data" / "state.json"

        JsonStore(path).save({"a": 1})

        self.assertTrue(path.exists())


class BrokenFileTests(JsonStoreTestCase):
    """Испорченный файл: программа работает дальше, но данные не теряются."""

    def write_broken_file(self) -> None:
        self.path.write_text('{"words": {"loop": ', encoding="utf-8")

    def test_broken_file_gives_empty_data(self):
        self.write_broken_file()

        self.assertEqual(JsonStore(self.path).load(), {})

    def test_broken_file_is_kept_as_backup_copy(self):
        self.write_broken_file()
        store = JsonStore(self.path)

        store.load()

        self.assertIsNotNone(store.backup_path)
        self.assertEqual(
            store.backup_path.read_text(encoding="utf-8"), '{"words": {"loop": '
        )

    def test_backup_copy_survives_next_save(self):
        """Раньше первый же ответ перезаписывал испорченный файл - и прогресс пропадал."""
        self.write_broken_file()
        store = JsonStore(self.path)
        store.load()

        store.save({"words": {}})

        self.assertTrue(store.backup_path.exists())

    def test_file_with_list_instead_of_object_is_treated_as_broken(self):
        self.path.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
        store = JsonStore(self.path)

        data = store.load()

        self.assertEqual(data, {})
        self.assertIsNotNone(store.backup_path)

    def test_good_file_makes_no_backup(self):
        JsonStore(self.path).save({"a": 1})
        store = JsonStore(self.path)

        store.load()

        self.assertIsNone(store.backup_path)


if __name__ == "__main__":
    unittest.main()
