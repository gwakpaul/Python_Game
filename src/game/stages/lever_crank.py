from __future__ import annotations

import math
import pygame

from ..core.stage_base import Stage


def _clamp_int(x: int, lo: int, hi: int) -> int:
    return lo if x < lo else hi if x > hi else x


def _angle_of(dx: float, dy: float) -> float:
    return math.atan2(dy, dx)


def _wrap_pi(a: float) -> float:
    while a <= -math.pi:
        a += 2.0 * math.pi
    while a > math.pi:
        a -= 2.0 * math.pi
    return a


class LeverCrankStage(Stage):
    stage_id: str = "lever_crank"

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

        # 레버 중심/길이
        self.center = (self.play_rect.centerx, self.play_rect.centery)
        self.handle_len = int(min(self.play_rect.width, self.play_rect.height) * 0.22)

        # 시각 두께/크기
        self.rod_width = 20
        self.knob_radius = 18
        self.pivot_radius = 10

        self.dragging = False
        self._last_angle = 0.0
        self._accum = 0.0
        self._visual_angle = 0.0

        self._rebuild_layout()

    def set_play_rect(self, play_rect: pygame.Rect) -> None:
        self.play_rect = play_rect.copy()
        self._rebuild_layout()

    def _rebuild_layout(self) -> None:
        self.center = (self.play_rect.centerx, self.play_rect.centery + 18)
        self.handle_len = int(min(self.play_rect.width, self.play_rect.height) * 0.22)

        # 화면이 작아져도 너무 짧아지지 않게
        self.handle_len = max(120, self.handle_len)

        # 두께도 약간 스케일
        base = min(self.play_rect.width, self.play_rect.height)
        self.rod_width = max(14, int(base * 0.035))
        self.knob_radius = max(14, int(base * 0.040))
        self.pivot_radius = max(8, int(base * 0.022))

    def supports_numeric_value(self) -> bool:
        return True

    def get_current_value(self) -> int:
        return int(self.current_value)

    def consume_volume_changed(self) -> bool:
        if self._volume_changed:
            self._volume_changed = False
            return True
        return False

    def _handle_tip_pos(self) -> tuple[int, int]:
        cx, cy = self.center
        hx = cx + math.cos(self._visual_angle) * self.handle_len
        hy = cy + math.sin(self._visual_angle) * self.handle_len
        return int(hx), int(hy)

    def _hit_test_handle(self, mx: int, my: int) -> bool:
        # 손잡이(노브) 근처만 잡히게
        hx, hy = self._handle_tip_pos()
        dx = mx - hx
        dy = my - hy
        r = max(16, int(self.knob_radius * 1.25))
        return (dx * dx + dy * dy) <= (r * r)

    def _apply_full_turns(self) -> None:
        full = 2.0 * math.pi

        while self._accum >= full:
            self._accum -= full
            if self.current_value < 100:
                self.current_value += 1
                self._volume_changed = True

        while self._accum <= -full:
            self._accum += full
            if self.current_value > 0:
                self.current_value -= 1
                self._volume_changed = True

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self._hit_test_handle(mx, my):
                self.dragging = True
                cx, cy = self.center
                self._last_angle = _angle_of(mx - cx, my - cy)
                return

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
            return

        if event.type == pygame.MOUSEMOTION and self.dragging:
            mx, my = event.pos
            cx, cy = self.center
            a = _angle_of(mx - cx, my - cy)

            da = _wrap_pi(a - self._last_angle)
            self._last_angle = a

            self._accum += da
            self._visual_angle += da

            self._apply_full_turns()

    def update(self, dt: float) -> None:
        super().update(dt)

    def render(self, screen: pygame.Surface) -> None:
        cx, cy = self.center
        hx, hy = self._handle_tip_pos()

        # 원형 구조 없이 "레버 막대 + 손잡이"만
        # 바깥 라인(테두리 느낌)
        pygame.draw.line(screen, (235, 235, 245), (cx, cy), (hx, hy), self.rod_width + 6)
        # 내부 막대
        pygame.draw.line(screen, (175, 175, 185), (cx, cy), (hx, hy), self.rod_width)

        # 피벗(작은 원)
        pygame.draw.circle(screen, (235, 235, 245), (cx, cy), self.pivot_radius + 3)
        pygame.draw.circle(screen, (110, 110, 125), (cx, cy), self.pivot_radius)

        # 손잡이(노브)
        pygame.draw.circle(screen, (235, 235, 245), (hx, hy), self.knob_radius + 3)
        pygame.draw.circle(screen, (185, 185, 195), (hx, hy), self.knob_radius)
        pygame.draw.circle(screen, (60, 60, 75), (hx, hy), self.knob_radius, 2)
