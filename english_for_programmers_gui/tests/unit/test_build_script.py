# Сборка exe (build_exe.py): прогресс exe-версии не должен пропадать.
#
# PyInstaller перед сборкой удаляет папку dist/EnglishForProgrammers целиком,
# а в ней лежит user_data/ с прогрессом exe-версии. Функция keep_user_data
# уносит user_data в сторону на время сборки и возвращает обратно.
#
# Здесь нет настоящей сборки: её работу изображает shutil.rmtree - ровно то,
# что PyInstaller делает с папкой программы.

import shutil
import tempfile
import unittest
from pathlib import Path

from build_exe import keep_user_data


class KeepUserDataTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="efp_build_script_")
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        self.app_dir = root / "dist" / "EnglishForProgrammers"
        self.backup_dir = root / "build" / "user_data_backup"
        self.progress = self.app_dir / "user_data" / "progress.json"

    def make_user_data(self) -> None:
        self.progress.parent.mkdir(parents=True)
        self.progress.write_text('{"words": {"loop": 3}}', encoding="utf-8")

    @staticmethod
    def rebuild(app_dir: Path) -> None:
        """То, что делает PyInstaller: стирает папку программы и создаёт заново."""
        shutil.rmtree(app_dir, ignore_errors=True)
        app_dir.mkdir(parents=True)

    def test_user_data_is_back_after_build(self):
        self.make_user_data()

        with keep_user_data(self.app_dir, self.backup_dir):
            self.rebuild(self.app_dir)

        self.assertEqual(
            self.progress.read_text(encoding="utf-8"), '{"words": {"loop": 3}}'
        )

    def test_user_data_is_out_of_harms_way_during_build(self):
        self.make_user_data()

        with keep_user_data(self.app_dir, self.backup_dir):
            self.assertFalse((self.app_dir / "user_data").exists())

    def test_user_data_is_back_even_if_build_fails(self):
        self.make_user_data()

        # Два with в одном: ждём ошибку И сберегаем данные.
        with (
            self.assertRaises(RuntimeError),
            keep_user_data(self.app_dir, self.backup_dir),
        ):
            shutil.rmtree(self.app_dir)
            raise RuntimeError("PyInstaller упал")

        self.assertTrue(self.progress.exists())

    def test_first_build_without_user_data_works(self):
        with keep_user_data(self.app_dir, self.backup_dir):
            self.rebuild(self.app_dir)

        self.assertFalse((self.app_dir / "user_data").exists())

    def test_backup_left_by_crashed_build_stops_new_build(self):
        """Если прошлая сборка оборвалась, в копии могут быть единственные данные.

        Новая сборка не должна их затереть: она останавливается и говорит,
        где лежит копия.
        """
        self.backup_dir.mkdir(parents=True)
        (self.backup_dir / "progress.json").write_text("{}", encoding="utf-8")
        self.make_user_data()

        with (
            self.assertRaisesRegex(RuntimeError, "user_data_backup"),
            keep_user_data(self.app_dir, self.backup_dir),
        ):
            pass

        self.assertTrue(self.progress.exists())
        self.assertTrue((self.backup_dir / "progress.json").exists())


if __name__ == "__main__":
    unittest.main()
