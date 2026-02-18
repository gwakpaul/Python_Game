from __future__ import annotations

import pygame

from ..core.scene_base import Scene
from ..ui.widgets import Button, Toast
from ..ui.header import Header


class ChallengeScene(Scene):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.toast = Toast()

        self.btn_home = Button(pygame.Rect(22, 18, 120, 42), "Home")
        self.btn_start = Button(pygame.Rect(0, 0, 420, 90), "START")

    def on_enter(self) -> None:
        self._layout()

    def _layout(self) -> None:
        self.btn_start.rect.center = (self.app.screen.get_width() // 2, 360)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.VIDEORESIZE:
            self._layout()

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            from .main_menu_scene import MainMenuScene
            self.app.change_scene(MainMenuScene(self.app))
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse = event.pos

            if self.btn_home.rect.collidepoint(mouse):
                from .main_menu_scene import MainMenuScene
                self.app.change_scene(MainMenuScene(self.app))
                return

            if self.btn_start.rect.collidepoint(mouse):
                self.toast.show("현재 플레이 가능한 스테이지가 10개 미만이다.")
                return

    def update(self, dt: float) -> None:
        self.toast.update(dt)

    def render(self, screen: pygame.Surface) -> None:
        screen.fill((18, 18, 22))
        mouse = pygame.mouse.get_pos()

        self.btn_home.render(screen, self.app.small_font, mouse)

        Header.render(
            screen=screen,
            title="Challenge Mode",
            subtitle="Random 10 stages (no duplicates) - time starts on START",
            title_font=self.app.base_font,
            subtitle_font=self.app.small_font,
        )

        # 설명은 헤더 아래 좌측에 두되, 헤더와 겹치지 않게 y=150부터
        lines = [
            "Start 버튼을 누르는 순간부터 시간이 측정된다.",
            "무작위 10개 스테이지를 중복 없이 클리어하면 기록이 확정된다.",
            "",
            "현재는 구현된 스테이지가 10개 미만이라 Start는 안내만 한다.",
        ]
        y = 150
        for line in lines:
            surf = self.app.small_font.render(line, True, (190, 190, 190))
            screen.blit(surf, (30, y))
            y += 26

        self.btn_start.render(screen, self.app.base_font, mouse)
        self.toast.render(screen, self.app.small_font)
