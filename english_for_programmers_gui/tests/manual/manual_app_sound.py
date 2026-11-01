import tempfile
from pathlib import Path
from types import SimpleNamespace

from gui.app import App
from tests.support import ROOT


def run():
    with tempfile.TemporaryDirectory(prefix="efp_visible_app_") as tmp:
        app = App(ROOT, Path(tmp) / "user_data")

        def start_and_speak():
            app.show_page("cards")
            cards = app.pages["cards"]
            cards.start_new()
            app.update()
            print(f"Текущее слово: {cards.word.answer} - {cards.word.ru}", flush=True)
            app._on_key(SimpleNamespace(keysym="p", keycode=80, state=0))
            print("Клавиша P отправлена в приложение.", flush=True)

        app.after(800, start_and_speak)
        app.mainloop()


if __name__ == "__main__":
    run()
