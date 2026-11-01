# =============================================================================
# НАСТРОЙКИ И СОСТОЯНИЕ - всё, что нужно запомнить между запусками
# =============================================================================
#
# Файл user_data/state.json:
#   тема оформления, размер окна, последняя тема,
#   незаконченные занятия по каждому режиму, место в разделе "Ошибки Python".

import json
from pathlib import Path

from core.session import Session


class Settings:
    def __init__(self, path: Path):
        self._path = path
        try:
            self._data = json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            self._data = {}

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(self._data, ensure_ascii=False, indent=1)
        self._path.write_text(text, encoding="utf-8")

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
