from __future__ import annotations

import pygame


class SliderChrome:
    """
    슬라이더형 스테이지의 공통 장식/배치를 담당.
    - 스피커(장식) + 슬라이더 바(통일 톤)
    """

    def __init__(self) -> None:
        self.speaker_rect = pygame.Rect(0, 0, 96, 96)
        self.speaker_gap = 12

        self.bar_fill_color = (215, 215, 215)

        # 테두리: 기존보다 약간 더 밝게(내부 흰색/밝은 회색과는 확실히 구분)
        self.bar_border_color = (140, 140, 160)

        self.bar_border_width = 2
        self.bar_radius = 10

    def layout_speaker_next_to_slider(self, play_rect: pygame.Rect, slider_rect: pygame.Rect) -> None:
        cx = play_rect.centerx + 20
        cy = play_rect.centery + 10
        slider_rect.center = (cx, cy)

        self.speaker_rect.right = slider_rect.left - self.speaker_gap
        self.speaker_rect.centery = slider_rect.centery

    def draw_slider_bar(self, screen: pygame.Surface, slider_rect: pygame.Rect) -> None:
        pygame.draw.rect(screen, self.bar_fill_color, slider_rect, border_radius=self.bar_radius)
        pygame.draw.rect(
            screen,
            self.bar_border_color,
            slider_rect,
            width=self.bar_border_width,
            border_radius=self.bar_radius,
        )

    def draw_speaker(self, screen: pygame.Surface, angle_deg: float = 0.0) -> None:
        w, h = self.speaker_rect.size
        surf = pygame.Surface((w, h), pygame.SRCALPHA)

        body = pygame.Rect(int(w * 0.10), int(h * 0.30), int(w * 0.20), int(h * 0.40))
        pygame.draw.rect(surf, (235, 235, 235), body, border_radius=6)

        horn = [
            (int(w * 0.30), int(h * 0.32)),
            (int(w * 0.78), int(h * 0.16)),
            (int(w * 0.78), int(h * 0.84)),
            (int(w * 0.30), int(h * 0.68)),
        ]
        pygame.draw.polygon(surf, (235, 235, 235), horn)

        pygame.draw.arc(
            surf,
            (210, 210, 210),
            pygame.Rect(int(w * 0.46), int(h * 0.26), int(w * 0.36), int(h * 0.48)),
            -0.75,
            0.75,
            2,
        )
        pygame.draw.arc(
            surf,
            (195, 195, 195),
            pygame.Rect(int(w * 0.40), int(h * 0.20), int(w * 0.44), int(h * 0.60)),
            -0.75,
            0.75,
            2,
        )

        rotated = pygame.transform.rotozoom(surf, -angle_deg, 1.0)
        r = rotated.get_rect(center=self.speaker_rect.center)
        screen.blit(rotated, r.topleft)
