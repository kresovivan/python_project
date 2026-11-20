# -*- coding: utf-8 -*-
"""Спрайт-атлас питомца.

Что это в жизни: "фотоплёнка". В одной длинной ленте лежат все движения
котика, а атлас знает, где какой кадр, и вырезает их по одному.

Атлас читает pet.json (там описаны строки и число кадров каждого движения)
и spritesheet.png (сама лента с кадрами).
"""

import json
from dataclasses import dataclass
from pathlib import Path

from PIL import Image


@dataclass(frozen=True)
class StateInfo:
    """Описание одного движения: строка в ленте, число кадров, скорость."""

    name: str
    row: int
    frames: int
    fps: float


class SpriteAtlas:
    """Вырезает кадры движений из большой картинки."""

    def __init__(self, manifest_path: Path, image_path: Path, scale: float = 0.5):
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
        self.frame_width = manifest["atlas"]["frameWidth"]
        self.frame_height = manifest["atlas"]["frameHeight"]
        self._states = {
            name: StateInfo(
                name=name,
                row=st["row"],
                frames=st["frames"],
                fps=float(st["fps"]),
            )
            for name, st in manifest["states"].items()
        }
        self._sheet = Image.open(image_path).convert("RGBA")
        # Кадры на экране уменьшаем - иначе котик займёт пол-экрана.
        self.out_width = max(1, int(self.frame_width * scale))
        self.out_height = max(1, int(self.frame_height * scale))
        self._cache = {}

    def state_names(self):
        """Имена всех движений, которые умеет питомец."""
        return list(self._states)

    def info(self, name: str) -> StateInfo:
        if name not in self._states:
            raise KeyError(f"в атласе нет движения {name!r}")
        return self._states[name]

    def frames(self, name: str):
        """Список кадров движения (картинки PIL), кэшируется."""
        if name in self._cache:
            return self._cache[name]
        st = self.info(name)
        result = []
        for i in range(st.frames):
            x = i * self.frame_width
            y = st.row * self.frame_height
            cell = self._sheet.crop((x, y, x + self.frame_width, y + self.frame_height))
            result.append(cell.resize((self.out_width, self.out_height), Image.LANCZOS))
        self._cache[name] = result
        return result
