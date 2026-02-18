from __future__ import annotations

import pygame


class Slider:
    """
    간단한 수평 슬라이더 (0~100 정수값)
    - 옵션 화면에서 사용
    """

    def __init__(self, rect: pygame.Rect, value: int = 50) -> None:
        self.rect = rect
        self.min_value = 0
        self.max_value = 100
        self.value = int(max(self.min_value, min(self.max_value, value)))
        self.dragging = False

    def set_value(self, v: int) -> None:
        v = int(v)
        self.value = max(self.min_value, min(self.max_value, v))

    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        값이 변경되면 True 반환
        """
        changed = False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                changed = self._set_from_mouse_x(event.pos[0])

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False

        elif event.type == pygame.MOUSEMOTION and self.dragging:
            changed = self._set_from_mouse_x(event.pos[0])

        return changed

    def _set_from_mouse_x(self, mx: int) -> bool:
        x0 = self.rect.left + 14
        x1 = self.rect.right - 14
        mx = max(x0, min(x1, mx))
        t = (mx - x0) / (x1 - x0) if x1 > x0 else 0.0
        new_value = int(round(self.min_value + t * (self.max_value - self.min_value)))
        if new_value != self.value:
            self.value = new_value
            return True
        return False

    def render(self, screen: pygame.Surface) -> None:
        # 바깥 프레임
        pygame.draw.rect(screen, (30, 30, 36), self.rect, border_radius=12)
        pygame.draw.rect(screen, (90, 90, 105), self.rect, width=2, border_radius=12)

        # 트랙
        track = pygame.Rect(self.rect.left + 14, self.rect.centery - 4, self.rect.width - 28, 8)
        pygame.draw.rect(screen, (70, 70, 85), track, border_radius=6)

        # 채움
        t = (self.value - self.min_value) / (self.max_value - self.min_value) if self.max_value > self.min_value else 0.0
        fill_w = int(track.width * t)
        fill = pygame.Rect(track.left, track.top, fill_w, track.height)
        pygame.draw.rect(screen, (150, 150, 175), fill, border_radius=6)

        # 핸들
        hx = track.left + fill_w
        hy = track.centery
        pygame.draw.circle(screen, (235, 235, 245), (hx, hy), 10)
        pygame.draw.circle(screen, (40, 40, 50), (hx, hy), 10, 2)
