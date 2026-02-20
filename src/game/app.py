from __future__ import annotations

import sys
import pygame

from .config import FPS
from .core.scene_base import Scene
from .systems.persist import load_settings


class App:
    def __init__(self, width: int, height: int, caption: str, flags: int = 0, vsync: int = 0) -> None:
        self.width = width
        self.height = height

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except Exception:
            pass

        self.screen = pygame.display.set_mode((width, height), flags=flags, vsync=vsync)
        pygame.display.set_caption(caption)

        self.clock = pygame.time.Clock()
        self.running = True

        self.scene: Scene | None = None

        self.base_font = pygame.font.SysFont("malgungothic", 30) or pygame.font.SysFont(None, 30)
        self.small_font = pygame.font.SysFont("malgungothic", 20) or pygame.font.SysFont(None, 20)

        self.master_volume = 0.5
        self.output_gain = 1.0

        try:
            s = load_settings()
            self.master_volume = float(s.get("master_volume", 50)) / 100.0
            self.output_gain = float(s.get("output_gain", 100)) / 100.0
        except Exception:
            pass

        self.apply_master_volume(self.master_volume)
        self.apply_output_gain(self.output_gain)

    def _apply_final_volume(self) -> None:
        final_v = float(self.master_volume) * float(self.output_gain)
        final_v = max(0.0, min(1.0, final_v))

        try:
            pygame.mixer.music.set_volume(final_v)
        except Exception:
            pass

    def apply_master_volume(self, volume_01: float) -> None:
        v = max(0.0, min(1.0, float(volume_01)))
        self.master_volume = v
        self._apply_final_volume()

    def apply_output_gain(self, gain_01: float) -> None:
        g = max(0.0, min(1.0, float(gain_01)))
        self.output_gain = g
        self._apply_final_volume()

    def change_scene(self, next_scene: Scene) -> None:
        if self.scene is not None:
            self.scene.on_exit()
        self.scene = next_scene
        self.scene.on_enter()

    def quit(self) -> None:
        self.running = False

    def run(self) -> None:
        while self.running:
            dt_ms = self.clock.tick(FPS)
            dt = dt_ms / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break
                if self.scene is not None:
                    self.scene.handle_event(event)

            if not self.running:
                break

            if self.scene is not None:
                self.scene.update(dt)
                self.scene.render(self.screen)

            pygame.display.flip()

        pygame.quit()
        sys.exit(0)
