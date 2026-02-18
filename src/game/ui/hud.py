from __future__ import annotations

import pygame


class HUD:
    """
    공통 HUD:
    - Stage i / N
    - Target / Current
    - Elapsed time
    """

    def __init__(self, app) -> None:
        self.app = app

    def render(
        self,
        screen: pygame.Surface,
        stage_index: int,
        stage_total: int,
        target: int,
        current: int,
        elapsed: float,
    ) -> None:
        text = f"Stage {stage_index}/{stage_total} | Target: {target} | Current: {current} | Time: {elapsed:.2f}s"
        surf = self.app.small_font.render(text, True, (235, 235, 235))
        screen.blit(surf, (20, 14))
