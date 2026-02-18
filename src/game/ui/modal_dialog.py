from __future__ import annotations

import pygame
from .widgets import Button


class ModalDialog:
    """
    단순 모달(성공/안내) 다이얼로그
    - 반투명 오버레이 + 중앙 패널 + 버튼 2개
    """

    def __init__(
        self,
        screen_size: tuple[int, int],
        title: str,
        message: str,
        left_button_text: str,
        right_button_text: str,
    ) -> None:
        self.screen_w, self.screen_h = screen_size
        self.title = title
        self.message = message

        panel_w = 520
        panel_h = 220
        self.panel_rect = pygame.Rect(0, 0, panel_w, panel_h)
        self.panel_rect.center = (self.screen_w // 2, self.screen_h // 2)

        btn_w = 180
        btn_h = 48
        gap = 18

        left_rect = pygame.Rect(0, 0, btn_w, btn_h)
        right_rect = pygame.Rect(0, 0, btn_w, btn_h)

        left_rect.center = (self.panel_rect.centerx - (btn_w // 2 + gap // 2), self.panel_rect.bottom - 56)
        right_rect.center = (self.panel_rect.centerx + (btn_w // 2 + gap // 2), self.panel_rect.bottom - 56)

        self.btn_left = Button(left_rect, left_button_text)
        self.btn_right = Button(right_rect, right_button_text)

    def resize(self, screen_size: tuple[int, int]) -> None:
        self.__init__(
            screen_size=screen_size,
            title=self.title,
            message=self.message,
            left_button_text=self.btn_left.text,
            right_button_text=self.btn_right.text,
        )

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """
        반환값:
        - "left" / "right" / None
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self.btn_left.rect.collidepoint(mx, my):
                return "left"
            if self.btn_right.rect.collidepoint(mx, my):
                return "right"
        return None

    def render(self, screen: pygame.Surface, title_font: pygame.font.Font, body_font: pygame.font.Font) -> None:
        # overlay
        overlay = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))

        # panel
        pygame.draw.rect(screen, (28, 28, 34), self.panel_rect, border_radius=16)
        pygame.draw.rect(screen, (90, 90, 105), self.panel_rect, width=2, border_radius=16)

        # text
        title_surf = title_font.render(self.title, True, (240, 240, 240))
        screen.blit(title_surf, (self.panel_rect.centerx - title_surf.get_width() // 2, self.panel_rect.top + 28))

        msg_surf = body_font.render(self.message, True, (210, 210, 210))
        screen.blit(msg_surf, (self.panel_rect.centerx - msg_surf.get_width() // 2, self.panel_rect.top + 88))

        mouse = pygame.mouse.get_pos()
        self.btn_left.render(screen, body_font, mouse)
        self.btn_right.render(screen, body_font, mouse)
