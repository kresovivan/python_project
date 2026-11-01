import statistics
import tempfile
import time
from pathlib import Path

from core import speech
from gui.app import App
from tests.support import ROOT


def run():
    speech.edge_tts = None
    with tempfile.TemporaryDirectory(prefix="efp_benchmark_") as tmp:
        app = App(ROOT, Path(tmp))
        try:
            keys = list(app.pages)
            for _ in range(2):
                for key in keys:
                    app.show_page(key)
                    app.update()
            measurements = {key: [] for key in keys}
            for _ in range(6):
                for key in keys:
                    started = time.perf_counter()
                    app.show_page(key)
                    app.update()
                    measurements[key].append((time.perf_counter() - started) * 1000)
            for key, values in measurements.items():
                print(
                    f"{key:10} медиана {statistics.median(values):6.1f} мс, "
                    f"среднее {statistics.mean(values):6.1f}, максимум {max(values):6.1f}"
                )
            resize = []
            app.show_page("home")
            for _ in range(3):
                for width, height in ((1200, 780), (1280, 820), (1120, 760), (1200, 780)):
                    started = time.perf_counter()
                    app.geometry(f"{width}x{height}")
                    app.update()
                    resize.append((time.perf_counter() - started) * 1000)
            print(
                f"Изменение размера: медиана {statistics.median(resize):.1f} мс, "
                f"среднее {statistics.mean(resize):.1f}, максимум {max(resize):.1f}"
            )
        finally:
            app.on_close()


if __name__ == "__main__":
    run()
