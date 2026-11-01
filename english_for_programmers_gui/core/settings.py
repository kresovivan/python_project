# =============================================================================
# НАСТРОЙКИ И СОСТОЯНИЕ - всё, что нужно запомнить между запусками
# =============================================================================
#
# Что это в жизни: "закладка и записка на холодильнике". Программа помнит,
# где вы остановились в каждом упражнении, какая была тема оформления,
# голос, размер и место окна.
#
# Файл user_data/state.json (читает и пишет JsonStore из core/storage.py):
#   тема оформления, размер окна, последняя тема, голос,
#   незаконченные занятия по каждому режиму, место в разделе "Ошибки Python".
#
# Кто пользуется: окно App (тема, окно), Lesson (место остановки),
# страницы (последняя тема, место в "Ошибках Python").

from pathlib import Path

from core.session import Session
from core.storage import JsonStore


class Settings:
    def __init__(self, path: Path):
        self._store = JsonStore(path)
        self._data = self._store.load()

    @property
    def backup_path(self) -> Path | None:
        """Куда отложен испорченный файл настроек (None - файл был в порядке)."""
        return self._store.backup_path

    def save(self) -> None:
        self._store.save(self._data)

    # --- простые значения ----------------------------------------------------
    # get/set - общие методы, остальные - удобные именованные обёртки.

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value) -> None:
        self._data[key] = value
        self.save()

    # --- незаконченные занятия -----------------------------------------------

    def session(self, mode: str) -> Session | None:
        """Незаконченное занятие режима mode (или None)."""
        data = self._data.get("sessions", {}).get(mode)
        return Session.from_dict(data) if data else None

    def save_session(self, session: Session) -> None:
        sessions = self._data.setdefault("sessions", {})
        if session.finished:
            sessions.pop(session.mode, None)  # законченное занятие не храним
        else:
            sessions[session.mode] = session.to_dict()
        self._data["last_mode"] = session.mode
        self.save()

    def drop_session(self, mode: str) -> None:
        self._data.get("sessions", {}).pop(mode, None)
        self.save()

    def last_session(self) -> Session | None:
        """Самое последнее незаконченное занятие - для кнопки 'Продолжить'."""
        last = self._data.get("last_mode")
        if last:
            session = self.session(last)
            if session:
                return session
        # последний режим уже завершён - берём любое другое незаконченное
        for mode in self._data.get("sessions", {}):
            return self.session(mode)
        return None
