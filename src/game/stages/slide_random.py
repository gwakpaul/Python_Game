from __future__ import annotations

import random
import pygame

from ..core.stage_base import Stage
from ..ui.slider_chrome import SliderChrome


def _clamp_int(x: int, lo: int, hi: int) -> int:
    return lo if x < lo else hi if x > hi else x


class SlideRandomStage(Stage):
    """
    7스테이지: 일반 슬라이더처럼 부드럽게 드래그 가능.
    단, 슬라이더의 위치(0~100 퍼센트)마다 "값(0~100)"이 랜덤하게 배정됨.

    - position_percent: 0~100 (노브 위치)
    - mapping[p]: p 위치에서의 값 (0~100), 랜덤 배정(예: mapping[0]=73, mapping[1]=4, ...)
    - current_value = mapping[position_percent]
    - 표시: 슬라이더 UI만 (하단 도움 표기 금지)
    """

    stage_id: str = "slide_random"

    def __init__(
        self,
        target: int,
        play_rect: pygame.Rect,
        mapping: list[int],
        initial_position_percent: int,
        hold_seconds: float = 0.5,
        clear_mode: str = "hold",
    ) -> None:
        super().__init__(target, hold_seconds=hold_seconds, clear_mode=clear_mode)

        self.play_rect = play_rect.copy()
        self.chrome = SliderChrome()

        # mapping은 길이 101 (0~100)
        if len(mapping) != 101:
            # 안전 폴백: 0~100 그대로
            mapping = list(range(101))

        self.mapping = [int(_clamp_int(v, 0, 100)) for v in mapping]

        self.slider_rect = pygame.Rect(0, 0, 600, 14)
        self.knob_radius = 9

        self.dragging = False

        self.position_percent = _clamp_int(int(initial_position_percent), 0, 100)
        self.current_value = int(self.mapping[self.position_percent])
        self._volume_changed = True

        self._rebuild_layout()

    def set_play_rect(self, play_rect: pygame.Rect) -> None:
        self.play_rect = play_rect.copy()
        self._rebuild_layout()

    def _rebuild_layout(self) -> None:
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

    def _percent_from_mouse_x(self, mx: int) -> int:
        left = self.slider_rect.left
        right = self.slider_rect.right
        if right <= left:
            return 0

        mx = _clamp_int(mx, left, right)
        t = (mx - left) / float(right - left)
        p = int(round(t * 100.0))
        return _clamp_int(p, 0, 100)

    def _knob_pos(self) -> tuple[int, int]:
        x = self.slider_rect.left + (self.position_percent / 100.0) * self.slider_rect.width
        y = self.slider_rect.centery
        return int(x), int(y)

    def _apply_position(self, new_percent: int) -> None:
        new_percent = _clamp_int(int(new_percent), 0, 100)
        if new_percent != self.position_percent:
            self.position_percent = new_percent
            self.current_value = int(self.mapping[self.position_percent])
            self._volume_changed = True

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self.slider_rect.collidepoint(mx, my):
                self.dragging = True
                self._apply_position(self._percent_from_mouse_x(mx))
                return

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
            return

        if event.type == pygame.MOUSEMOTION and self.dragging:
            mx, my = event.pos
            self._apply_position(self._percent_from_mouse_x(mx))

    def update(self, dt: float) -> None:
        super().update(dt)

    def render(self, screen: pygame.Surface) -> None:
        self.chrome.draw_speaker(screen, angle_deg=0.0)
        self.chrome.draw_slider_bar(screen, self.slider_rect)

        kx, ky = self._knob_pos()
        pygame.draw.circle(screen, (245, 245, 245), (kx, ky), self.knob_radius)
        pygame.draw.circle(screen, (140, 140, 150), (kx, ky), self.knob_radius, 2)


def make_random_mapping_0_100() -> list[int]:
    """
    0~100의 각 위치(퍼센트)에 0~100 값이 랜덤하게 배정되도록 만든다.
    - 결과 리스트 길이: 101
    - 각 값은 0~100이 정확히 한 번씩 등장(셔플)
    """
    values = list(range(101))
    random.shuffle(values)
    return values
