"""Переиспользуемые виджеты и миксины."""

from typing import List, Optional

import tkinter as tk

from ..constants import COLORS


class CopyableLabel(tk.Label):
    """Метка, значение которой можно скопировать.

    - правый клик -> контекстное меню (Копировать / Вставить в поиск);
    - двойной клик -> копирует значение в буфер.
    """

    def __init__(self, parent, text: str, app=None,
                 copy_value: Optional[str] = None, **kwargs):
        super().__init__(parent, text=text, **kwargs)
        self._full_text = text
        self._copy_text = text if copy_value is None else copy_value
        self._has_copy_value = copy_value is not None
        self._app = app
        self.bind('<Button-3>', self._context_menu)
        self.bind('<Double-Button-1>', lambda *_: self._copy())
        self.configure(cursor='hand2')

    def _context_menu(self, event) -> None:
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label='Копировать', command=self._copy)
        if self._has_copy_value:
            menu.add_command(label='Копировать строку целиком',
                             command=self._copy_full)
        if self._app is not None:
            menu.add_command(label='Копировать и вставить в поиск',
                             command=self._copy_and_paste)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _copy(self) -> None:
        self._clipboard_set(self._copy_text)

    def _copy_full(self) -> None:
        self._clipboard_set(self._full_text)

    def _copy_and_paste(self) -> None:
        self._copy()
        try:
            self._app._paste_to_search()
        except Exception:
            pass

    def _clipboard_set(self, value: str) -> None:
        try:
            self.clipboard_clear()
            self.clipboard_append(value)
            self.update()
        except tk.TclError:
            pass


class CardFrame(tk.Frame):
    """Рамка-«карточка»: белый фон панели + тонкая граница."""

    def __init__(self, parent, **kwargs):
        kwargs.setdefault('bg', COLORS['panel'])
        kwargs.setdefault('highlightthickness', 1)
        kwargs.setdefault('highlightbackground', COLORS['border'])
        super().__init__(parent, **kwargs)


class ScrollableMixin:
    """Миксин: привязывает колесо мыши к указанному Canvas.

    Наследник должен создать self._scroll_canvas и self._wheel_widgets
    перед вызовом _bind_wheel_recursive.
    """

    _wheel_widgets: List[tk.Widget]
    _scroll_canvas: tk.Canvas

    def _bind_wheel_recursive(self, widget: tk.Widget) -> None:
        try:
            widget.bind('<MouseWheel>', self._on_wheel)
        except Exception:
            pass
        self._wheel_widgets.append(widget)
        for child in widget.winfo_children():
            self._bind_wheel_recursive(child)

    def _unbind_wheel_all(self) -> None:
        for w in self._wheel_widgets:
            try:
                w.unbind('<MouseWheel>')
            except Exception:
                pass
        self._wheel_widgets.clear()

    def _on_wheel(self, event) -> str:
        """Прокрутка Canvas только если содержимое не помещается."""
        try:
            first, last = self._scroll_canvas.yview()
            if first <= 0.0 and last >= 1.0:
                return 'break'
            self._scroll_canvas.yview_scroll(
                int(-1 * (event.delta / 120)), 'units')
        except Exception:
            pass
        return 'break'