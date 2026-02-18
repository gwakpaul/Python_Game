from __future__ import annotations

import pygame

from ..core.stage_base import Stage
from ..ui.slider_chrome import SliderChrome


def _clamp_int(x: int, lo: int, hi: int) -> int:
    return lo if x < lo else hi if x > hi else x


class SliderNormalStage(Stage):
    stage_id: str = "slider_normal"

    def __init__(
        self,
        target: int,
        play_rect: pygame.Rect,
        initial_value: int = 50,
        hold_seconds: float = 0.5,
        clear_mode: str = "hold",
    ) -> None:
        super().__init__(target, hold_seconds=hold_seconds, clear_mode=clear_mode)

        self.play_rect = play_rect.copy()

        self.current_value = _clamp_int(int(initial_value), 0, 100)
        self._volume_changed = True

        # 공통 슬라이더 UI(스피커 장식 포함)
        self.chrome = SliderChrome()

        # 슬라이더 바는 기본 포맷(다른 슬라이더형 스테이지와 통일)
        self.slider_rect = pygame.Rect(0, 0, 600, 14)
        self.knob_radius = 9

        self.dragging = False

        self._rebuild_layout()

    def set_play_rect(self, play_rect: pygame.Rect) -> None:
        self.play_rect = play_rect.copy()
        self._rebuild_layout()

    def _rebuild_layout(self) -> None:
        # 스피커+슬라이더 배치(프로젝트 통일 함수)
        self.chrome.layout_speaker_next_to_slider(self.play_rect, self.slider_rect)

    def supports_numeric_value(self) -> bool:
        return True

    def get_current_value(self) -> int:
        return int(self.current_value)

    def consume_volume_changed(self) -> bool:
        if self._volume_changed:
            self._volume_changed = False
            return True
        return False

    def _value_from_mouse_x(self, x: int) -> int:
        left = self.slider_rect.left
        right = self.slider_rect.right
        if right <= left:
            return 0
        ratio = (x - left) / float(right - left)
        ratio = max(0.0, min(1.0, ratio))
        return int(round(ratio * 100.0))

    def _knob_pos(self) -> tuple[int, int]:
        x = self.slider_rect.left + (self.current_value / 100.0) * self.slider_rect.width
        y = self.slider_rect.centery
        return int(x), int(y)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self.slider_rect.collidepoint(mx, my):
                self.dragging = True
                new_value = self._value_from_mouse_x(mx)
                if new_value != self.current_value:
                    self.current_value = new_value
                    self._volume_changed = True
                return

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
            return

        if event.type == pygame.MOUSEMOTION and self.dragging:
            mx, my = event.pos
            new_value = self._value_from_mouse_x(mx)
            if new_value != self.current_value:
                self.current_value = new_value
                self._volume_changed = True

    def update(self, dt: float) -> None:
        super().update(dt)

    def render(self, screen: pygame.Surface) -> None:
        # 스피커 장식(상호작용 없음)
        self.chrome.draw_speaker(screen, angle_deg=0.0)

        # 슬라이더 바(통일 룩)
        self.chrome.draw_slider_bar(screen, self.slider_rect)

        # 노브
        kx, ky = self._knob_pos()
        pygame.draw.circle(screen, (245, 245, 245), (kx, ky), self.knob_radius)
        pygame.draw.circle(screen, (140, 140, 150), (kx, ky), self.knob_radius, 2)
