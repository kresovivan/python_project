# =============================================================================
# ВСПЛЫВАЮЩЕЕ СООБЩЕНИЕ внизу окна ("Загружаю произношение...", ошибки)
# =============================================================================

import customtkinter as ctk

from gui import theme


class Toast(ctk.CTkLabel):
    INFO = "info"
    ERROR = "error"

    def __init__(self, master):
        super().__init__(master, text="", font=theme.BODY, corner_radius=20, height=40)
        self._hide_id = None

    def show(self, text: str, kind: str = ERROR, ms: int = 2500) -> None:
        """Показать сообщение на ms миллисекунд. kind - Toast.INFO или Toast.ERROR."""
        if kind == self.ERROR:
            colors = dict(fg_color=theme.DANGER, text_color=theme.ON_DANGER)
        else:
            colors = dict(fg_color=theme.ACCENT, text_color=theme.ON_ACCENT)
        self.configure(text=f"     {text}     ", **colors)
        self.place(relx=0.5, rely=1.0, anchor="s", y=-24)
        self.lift()  # поверх страниц
        if self._hide_id:
            self.after_cancel(self._hide_id)
        self._hide_id = self.after(ms, self.place_forget)
