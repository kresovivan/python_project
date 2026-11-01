# =============================================================================
# ДЕРЖАТЕЛЬ СТРАНИЦ - создаёт страницы и показывает одну из них
# =============================================================================

from gui import theme
from gui.context import AppContext
from gui.pages.base import Page
from gui.widgets import Box


class PageHost(Box):
    """Все страницы занимают одну клетку сетки, но видна только одна.

    grid_remove() убирает страницу из раскладки, запомнив её настройки:
    скрытая страница не перерисовывается, когда меняется размер окна.
    """

    def __init__(self, master, page_classes: list[type[Page]], context: AppContext):
        super().__init__(master, color=theme.BG)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.pages: dict[str, Page] = {}
        self.current: Page | None = None
        for number, page_class in enumerate(page_classes, start=1):
            # Номер страницы = её место в меню. Задаём его классу ДО создания
            # страницы: шапка страницы "02 / КАРТОЧКИ" строится в __init__.
            page_class.number = number
            page = page_class(self, context)
            page.grid(row=0, column=0, sticky="nsew")
            page.grid_remove()
            self.pages[page_class.key] = page

    @property
    def keys(self) -> list[str]:
        return list(self.pages)

    def show(self, key: str) -> Page | None:
        """Показать страницу key. Вернёт страницу, которая была открыта до этого."""
        previous = self.current
        page = self.pages[key]
        if previous is page:
            page.on_show()  # та же страница - только обновить данные
            return previous
        if previous:
            previous.on_hide()
        self.current = page
        page.on_show()  # полиморфизм: у каждой страницы свой on_show
        # Сначала показываем новую страницу, потом прячем старую - без мигания.
        page.grid()
        if previous:
            previous.grid_remove()
        return previous

    def neighbour(self, step: int) -> str:
        """Ключ соседней страницы: step=1 - следующая, -1 - предыдущая (по кругу)."""
        index = self.keys.index(self.current.key)
        return self.keys[(index + step) % len(self.keys)]

    def title(self, key: str) -> str:
        return self.pages[key].title if key in self.pages else key
