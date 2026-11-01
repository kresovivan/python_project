# Настройки и незаконченные занятия (core/settings.py, файл state.json).

import tempfile
import unittest
from pathlib import Path

from core.session import Session
from core.settings import Settings


class SettingsTestCase(unittest.TestCase):
    """Общая подготовка: пустая временная папка для state.json."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="efp_settings_")
        self.addCleanup(tmp.cleanup)  # папка удалится после теста, даже если он упадёт
        self.path = Path(tmp.name) / "state.json"

    def reopen(self) -> Settings:
        """Прочитать настройки заново из файла - как при следующем запуске программы."""
        return Settings(self.path)


class SimpleValuesTests(SettingsTestCase):
    def test_missing_file_gives_default_values(self):
        settings = Settings(self.path)

        self.assertIsNone(settings.get("theme"))
        self.assertEqual(settings.get("theme", "Dark"), "Dark")

    def test_broken_file_gives_default_values(self):
        """Испорченный файл не должен ронять программу."""
        self.path.write_text("{bad json", encoding="utf-8")

        settings = Settings(self.path)

        self.assertIsNone(settings.get("theme"))

    def test_value_is_kept_after_restart(self):
        Settings(self.path).set("theme", "Light")

        self.assertEqual(self.reopen().get("theme"), "Light")


class SavedSessionTests(SettingsTestCase):
    def test_unfinished_session_is_kept_after_restart(self):
        session = Session("cards", "Тема", ["a", "b"], index=1, right=1)

        Settings(self.path).save_session(session)

        self.assertEqual(self.reopen().session("cards"), session)

    def test_finished_session_is_not_kept(self):
        """Законченное занятие продолжать нечего, его не храним."""
        settings = Settings(self.path)
        settings.save_session(Session("cards", "Тема", ["a"]))

        settings.save_session(Session("cards", "Тема", ["a"], index=1))

        self.assertIsNone(self.reopen().session("cards"))

    def test_sessions_of_different_modes_are_kept_separately(self):
        settings = Settings(self.path)
        cards = Session("cards", "Тема", ["a"])
        typing = Session("typing", "Тема", ["b"])

        settings.save_session(cards)
        settings.save_session(typing)

        self.assertEqual(self.reopen().session("cards"), cards)
        self.assertEqual(self.reopen().session("typing"), typing)

    def test_dropped_session_is_forgotten(self):
        settings = Settings(self.path)
        settings.save_session(Session("cards", "Тема", ["a"]))

        settings.drop_session("cards")

        self.assertIsNone(self.reopen().session("cards"))


class LastSessionTests(SettingsTestCase):
    """last_session() - занятие для кнопки "Продолжить" на главной."""

    def test_no_sessions_means_nothing_to_continue(self):
        self.assertIsNone(Settings(self.path).last_session())

    def test_last_saved_session_is_continued(self):
        settings = Settings(self.path)
        settings.save_session(Session("cards", "Тема", ["a"]))
        settings.save_session(Session("typing", "Тема", ["b"]))

        self.assertEqual(settings.last_session().mode, "typing")

    def test_other_unfinished_session_is_offered_when_last_one_is_finished(self):
        settings = Settings(self.path)
        settings.save_session(Session("cards", "Тема", ["a"]))
        settings.save_session(Session("typing", "Тема", ["b"]))

        finished_typing = Session("typing", "Тема", ["b"], index=1)
        settings.save_session(finished_typing)

        self.assertEqual(settings.last_session().mode, "cards")


if __name__ == "__main__":
    unittest.main()
