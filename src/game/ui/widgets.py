from __future__ import annotations

import pygame


class Button:
    def __init__(self, rect: pygame.Rect, text: str) -> None:
        self.rect = rect
        self.text = text
        self.enabled = True

    def is_hovered(self, mouse_pos: tuple[int, int]) -> bool:
        return self.rect.collidepoint(mouse_pos)

    def render(self, screen: pygame.Surface, font: pygame.font.Font, mouse_pos: tuple[int, int]) -> None:
        hovered = self.enabled and self.is_hovered(mouse_pos)

        if not self.enabled:
            bg = (70, 70, 80)
            fg = (150, 150, 160)
        else:
            bg = (95, 95, 110) if hovered else (75, 75, 90)
            fg = (235, 235, 235)

        pygame.draw.rect(screen, bg, self.rect, border_radius=10)
        pygame.draw.rect(screen, (35, 35, 45), self.rect, width=2, border_radius=10)

        surf = font.render(self.text, True, fg)
        screen.blit(surf, surf.get_rect(center=self.rect.center))


class Toast:
    def __init__(self) -> None:
        self.message = ""
        self.remaining = 0.0

    def show(self, message: str, seconds: float = 1.5) -> None:
        self.message = message
        self.remaining = seconds

    def update(self, dt: float) -> None:
        if self.remaining > 0.0:
            self.remaining -= dt
            if self.remaining <= 0.0:
                self.message = ""

    def render(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        if not self.message:
            return
        padding = 14
        surf = font.render(self.message, True, (240, 240, 240))
        rect = surf.get_rect()
        box = pygame.Rect(0, 0, rect.width + padding * 2, rect.height + padding * 2)
        box.center = (screen.get_width() // 2, screen.get_height() - 60)

        pygame.draw.rect(screen, (30, 30, 36), box, border_radius=12)
        pygame.draw.rect(screen, (80, 80, 95), box, width=2, border_radius=12)
        screen.blit(surf, surf.get_rect(center=box.center))
