# -*- coding: utf-8 -*-
"""Тесты спрайт-атласа: все движения на месте, кадры вырезаются."""

import unittest
from pathlib import Path

from core.atlas import SpriteAtlas

ASSETS = Path(__file__).resolve().parent.parent / "assets"

# Движения, которые обязаны быть в атласе.
EXPECTED_STATES = {
    "idle", "working", "waiting", "failed",
    "running_left", "running_right",
    "idle_random_1", "idle_random_2",
    "celebrate", "somersault", "paw_wave", "fish_snack", "annoyed",
}


class TestSpriteAtlas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.atlas = SpriteAtlas(ASSETS / "pet.json", ASSETS / "spritesheet.png", scale=0.5)

    def test_all_states_present(self):
        """Все нужные движения есть в атласе."""
        missing = EXPECTED_STATES - set(self.atlas.state_names())
        self.assertFalse(missing, f"в атласе не хватает движений: {missing}")

    def test_frames_count_and_size(self):
        """У каждого движения кадров столько, сколько написано в pet.json,
        и каждый кадр нужного размера."""
        for name in self.atlas.state_names():
            info = self.atlas.info(name)
            frames = self.atlas.frames(name)
            self.assertEqual(len(frames), info.frames, name)
            for frame in frames:
                self.assertEqual(frame.size, (self.atlas.out_width, self.atlas.out_height), name)
                self.assertEqual(frame.mode, "RGBA", name)

    def test_idle_has_visible_pixels(self):
        """В кадрах idle есть непрозрачные пиксели - котик виден."""
        import numpy as np
        frame = self.atlas.frames("idle")[0]
        alpha = np.asarray(frame)[..., 3]
        self.assertGreater(int((alpha > 0).sum()), 1000)

    def test_unknown_state_raises(self):
        with self.assertRaises(KeyError):
            self.atlas.frames("нет_такого")


if __name__ == "__main__":
    unittest.main()
