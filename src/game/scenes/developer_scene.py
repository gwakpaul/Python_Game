from __future__ import annotations

import pygame

from ..core.scene_base import Scene
from ..ui.widgets import Button
from ..ui.header import Header


class DeveloperScene(Scene):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.btn_home = Button(pygame.Rect(22, 18, 120, 42), "Home")

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            from .main_menu_scene import MainMenuScene
            self.app.change_scene(MainMenuScene(self.app))
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_home.rect.collidepoint(event.pos):
                from .main_menu_scene import MainMenuScene
                self.app.change_scene(MainMenuScene(self.app))
                return

    def render(self, screen: pygame.Surface) -> None:
        screen.fill((18, 18, 22))
        mouse = pygame.mouse.get_pos()

        self.btn_home.render(screen, self.app.small_font, mouse)

        Header.render(
            screen=screen,
            title="Developer",
            subtitle="Placeholder area for images / text",
            title_font=self.app.base_font,
            subtitle_font=self.app.small_font,
        )

        box = pygame.Rect(60, 160, screen.get_width() - 120, screen.get_height() - 240)
        pygame.draw.rect(screen, (30, 30, 36), box, border_radius=14)
        pygame.draw.rect(screen, (80, 80, 95), box, width=2, border_radius=14)

        lines = [
            "여기는 나중에 이미지/텍스트를 넣을 공간이다.",
            "예: 제작자 소개, 링크, 크레딧, 업데이트 노트 등",
        ]
        y = 190
        for line in lines:
            surf = self.app.small_font.render(line, True, (200, 200, 200))
            screen.blit(surf, (80, y))
            y += 28
