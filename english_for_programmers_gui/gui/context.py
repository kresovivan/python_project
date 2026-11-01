# =============================================================================
# КОНТЕКСТ ПРИЛОЖЕНИЯ - всё, что нужно странице, в одном объекте
# =============================================================================
#
# Раньше каждая страница получала ВСЁ окно App и брала из него что хотела
# (self.app.progress, self.app.say, self.app.show_page ...). Из-за этого
# страницы зависели от устройства окна: поменял App - сломал страницы.
#
# Теперь страница получает AppContext - короткий список того, чем ей можно
# пользоваться. Видно сразу, от чего она зависит, а App можно менять свободно.
# Такой приём называется "внедрение зависимостей" (dependency injection).

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:  # импорты только для подсказок типов, без циклических импортов
    from core.models import ErrorMessage
    from core.progress import Progress
    from core.settings import Settings
    from core.vocabulary import Vocabulary
    from gui.voice import VoiceController


class Navigator(Protocol):
    """То, что страница может попросить у окна: перейти на другую страницу.

    Protocol - это "договор": любой объект с такими методами подходит,
    наследоваться от Navigator не обязательно. Окно App этот договор выполняет.
    """

    def show_page(self, key: str) -> None: ...

    def page_title(self, key: str) -> str: ...


@dataclass(frozen=True)
class AppContext:
    vocabulary: Vocabulary  # слова
    progress: Progress  # статистика ответов
    settings: Settings  # настройки и место остановки
    errors: list[ErrorMessage]  # ошибки Python для страницы "Ошибки Python"
    voice: VoiceController  # озвучка
    navigator: Navigator  # переход между страницами
