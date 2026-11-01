# =============================================================================
# СПРАВКА ПО ГОРЯЧИМ КЛАВИШАМ - слой поверх окна (F1)
# =============================================================================
#
# Что это в жизни: "шпаргалка, которую кладут поверх тетради". Список
# сочетаний берётся из HELP (gui/hotkeys.py): данные отдельно от окна.
#
# Это обычная рамка, которую "кладут" поверх всего окна методом place()
# и убирают методом place_forget(). Отдельное окно не нужно.
# Текст выводится в два поля RichText (левая и правая колонка), а не
# в десятки отдельных меток: так справка открывается мгновенно.

from gui import hotkeys, theme
from gui.widgets import Box, Card, Muted, RichText, Title

KEY_COLUMN = 180  # ширина колонки с клавишами (до масштабирования)


class HelpOverlay(Box):
    def __init__(self, master):
        super().__init__(master, color=theme.BG)

        card = Card(self)
        card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.86, relheight=0.9)

        header = Box(card, color=theme.CARD)
        header.pack(fill="x", padx=30, pady=(24, 4))
        Title(header, "Горячие клавиши", font=theme.H2).pack(side="left")
        Muted(header, "F1 или Esc - закрыть", font=theme.SMALL).pack(side="right")

        columns = Box(card, color=theme.CARD)
        columns.pack(fill="both", expand=True, padx=12, pady=(0, 16))
        columns.columnconfigure((0, 1), weight=1, uniform="col")
        columns.rowconfigure(0, weight=1)

        self.boxes = []
        for column in (0, 1):
            box = RichText(columns, border_width=0)
            box.grid(row=0, column=column, sticky="nsew")
            self.boxes.append(box)

        # Разделы по очереди: 0-й слева, 1-й справа, 2-й слева...
        for column, box in enumerate(self.boxes):
            box.define("section", font=theme.H3, fg=theme.ACCENT, spacing1=14, spacing3=6)
            box.define("keys", font=(theme.MONO, 13, "bold"), fg=theme.TEXT, bg=theme.CARD_ALT)
            # lmargin2 - отступ для перенесённых строк описания: они встают
            # ровно под началом описания, а не под клавишами.
            box.define("action", font=theme.BODY, fg=theme.MUTED, lmargin2=KEY_COLUMN, spacing3=6)
            chunks = []
            for section, items in hotkeys.HELP[column::2]:
                chunks.append((section + "\n", "section"))
                for keys, action in items:
                    chunks += [(f" {keys} ", "keys"), ("\t" + action + "\n", "action")]
            box.write(chunks)

        self.visible = False

    def toggle(self) -> None:
        if self.visible:
            self.hide()
        else:
            self.show()

    def show(self) -> None:
        for box in self.boxes:
            box.restyle()  # тема оформления могла смениться
            box.text.configure(tabs=(box.px(KEY_COLUMN),))
        self.visible = True
        self.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.lift()  # поверх всех остальных элементов окна

    def hide(self) -> None:
        self.visible = False
        self.place_forget()
