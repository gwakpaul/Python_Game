from __future__ import annotations

import pygame

from ..core.scene_base import Scene
from ..core.run_controller import RunController
from ..ui.hud import HUD


class RunScene(Scene):
    """
    10-run 진행 씬(최소):
    - 현재 Stage(기믹)를 실행
    - 클리어 시 다음 Stage로 이동
    - 10개 완료 시 메인 메뉴로 복귀(임시)
    """

    def __init__(self, app) -> None:
        super().__init__(app)
        self.controller = RunController(seed=None, stage_count=10)
        self.stage = None
        self.hud = HUD(app)
        self.elapsed = 0.0

    def on_enter(self) -> None:
        self._advance_stage()

    def _advance_stage(self) -> None:
        if self.controller.has_next():
            self.stage = self.controller.next_stage()
        else:
            # 임시: 완료 후 메뉴로 복귀
            from .main_menu_scene import MainMenuScene
            self.app.change_scene(MainMenuScene(self.app))

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            # 임시: ESC는 메뉴로
            from .main_menu_scene import MainMenuScene
            self.app.change_scene(MainMenuScene(self.app))
            return

        if self.stage is not None:
            self.stage.handle_event(event)

    def update(self, dt: float) -> None:
        self.elapsed += dt

        if self.stage is None:
            return

        self.stage.update(dt)

        if self.stage.is_cleared():
            self._advance_stage()

    def render(self, screen: pygame.Surface) -> None:
        screen.fill((10, 10, 12))

        if self.stage is None:
            return

        self.stage.render(screen)

        stage_index = self.controller.index
        self.hud.render(
            screen=screen,
            stage_index=stage_index,
            stage_total=self.controller.stage_count,
            target=self.stage.get_target_value(),
            current=self.stage.get_current_value(),
            elapsed=self.elapsed,
        )
