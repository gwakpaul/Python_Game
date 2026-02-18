from __future__ import annotations

import math
import pygame

from ..core.stage_base import Stage
from ..ui.slider_chrome import SliderChrome


def _clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


def _project_t_on_segment(p: pygame.Vector2, a: pygame.Vector2, b: pygame.Vector2) -> float:
    ab = b - a
    ab_len2 = ab.x * ab.x + ab.y * ab.y
    if ab_len2 <= 1e-9:
        return 0.0
    t = ((p - a).x * ab.x + (p - a).y * ab.y) / ab_len2
    return _clamp(t, 0.0, 1.0)


def _point_segment_distance(p: pygame.Vector2, a: pygame.Vector2, b: pygame.Vector2) -> float:
    ab = b - a
    ab_len2 = ab.x * ab.x + ab.y * ab.y
    if ab_len2 <= 1e-9:
        return (p - a).length()
    t = ((p - a).x * ab.x + (p - a).y * ab.y) / ab_len2
    t = _clamp(t, 0.0, 1.0)
    proj = a + ab * t
    return (p - proj).length()


class TiltSliderStage(Stage):
    stage_id: str = "tilt_slider"

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

        self.chrome = SliderChrome()

        self.pos = _clamp(float(initial_value) / 100.0, 0.0, 1.0)
        self.vel = 0.0

        self.current_value = int(round(self.pos * 100.0))
        self._volume_changed = True

        self.angle_deg = 0.0
        self.angle_min = -75.0
        self.angle_max = 75.0

        self.dragging = False
        self._grab_s = 0.0
        self._grab_deadzone = 10.0

        self.bar_length = 580
        self.bar_thickness = 14
        self.ball_radius = 10
        self.hit_thickness = 22

        self.fit_margin = 18

        self.g_eff = 5.8
        self.damping = 2.4

        # 회전 막대(둥근 직사각형) 렌더용 베이스 서피스
        self._bar_base = None
        self._build_bar_surface()

        self._rebuild_layout()

    def _build_bar_surface(self) -> None:
        # 회전 시 가장자리가 잘리지 않도록 약간 크게 만든다.
        w = int(self.bar_length + self.bar_thickness * 3)
        h = int(self.bar_thickness + self.bar_thickness * 3)
        surf = pygame.Surface((w, h), pygame.SRCALPHA)

        rect = pygame.Rect(0, 0, self.bar_length, self.bar_thickness)
        rect.center = (w // 2, h // 2)

        pygame.draw.rect(surf, (215, 215, 215), rect, border_radius=10)
        # 테두리 느낌
        pygame.draw.rect(surf, (160, 160, 170), rect, width=2, border_radius=10)

        self._bar_base = surf

    def set_play_rect(self, play_rect: pygame.Rect) -> None:
        self.play_rect = play_rect.copy()
        self._rebuild_layout()

    def _rebuild_layout(self) -> None:
        dummy_slider_rect = pygame.Rect(0, 0, 600, 14)
        self.chrome.layout_speaker_next_to_slider(self.play_rect, dummy_slider_rect)
        self.center = pygame.Vector2(dummy_slider_rect.centerx, dummy_slider_rect.centery)

    def supports_numeric_value(self) -> bool:
        return True

    def get_current_value(self) -> int:
        return int(self.current_value)

    def consume_volume_changed(self) -> bool:
        if self._volume_changed:
            self._volume_changed = False
            return True
        return False

    def _endpoints_for_angle(self, angle_deg: float) -> tuple[pygame.Vector2, pygame.Vector2]:
        rad = math.radians(angle_deg)
        half = self.bar_length * 0.5
        dx = math.cos(rad) * half
        dy = math.sin(rad) * half
        left = pygame.Vector2(self.center.x - dx, self.center.y - dy)
        right = pygame.Vector2(self.center.x + dx, self.center.y + dy)
        return left, right

    def _endpoints(self) -> tuple[pygame.Vector2, pygame.Vector2]:
        return self._endpoints_for_angle(self.angle_deg)

    def _ball_world_pos(self) -> pygame.Vector2:
        left, right = self._endpoints()
        return left + (right - left) * self.pos

    def _hit_test_bar(self, mx: int, my: int) -> bool:
        p = pygame.Vector2(mx, my)
        a, b = self._endpoints()
        d = _point_segment_distance(p, a, b)
        return d <= float(self.hit_thickness)

    def _compute_grab_s(self, mx: int, my: int) -> float:
        p = pygame.Vector2(mx, my)
        left, right = self._endpoints()
        t = _project_t_on_segment(p, left, right)
        half = self.bar_length * 0.5
        s = (t - 0.5) * (2.0 * half)
        return float(s)

    def _angle_from_mouse_for_grab(self, mx: int, my: int) -> float:
        v = pygame.Vector2(mx, my) - self.center
        if v.length_squared() <= 1e-6:
            return self.angle_deg

        ang = math.degrees(math.atan2(v.y, v.x))
        if self._grab_s < 0.0:
            ang += 180.0

        while ang > 180.0:
            ang -= 360.0
        while ang < -180.0:
            ang += 360.0

        ang = float(_clamp(ang, self.angle_min, self.angle_max))
        ang = self._clamp_angle_to_fit(float(ang))
        return ang

    def _angle_fits_in_frame(self, angle_deg: float) -> bool:
        a, b = self._endpoints_for_angle(angle_deg)
        inner = self.play_rect.inflate(-2 * self.fit_margin, -2 * self.fit_margin)
        return inner.collidepoint(int(a.x), int(a.y)) and inner.collidepoint(int(b.x), int(b.y))

    def _clamp_angle_to_fit(self, desired_angle: float) -> float:
        desired_angle = float(_clamp(desired_angle, self.angle_min, self.angle_max))
        if self._angle_fits_in_frame(desired_angle):
            return desired_angle

        sign = 1.0 if desired_angle >= 0.0 else -1.0
        hi = abs(desired_angle)
        lo = 0.0
        best = 0.0

        for _ in range(14):
            mid = (lo + hi) * 0.5
            test = sign * mid
            if self._angle_fits_in_frame(test):
                best = mid
                lo = mid
            else:
                hi = mid

        return sign * best

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self._hit_test_bar(mx, my):
                s = self._compute_grab_s(mx, my)
                if abs(s) < self._grab_deadzone:
                    self.dragging = False
                    return
                self.dragging = True
                self._grab_s = s
                self.angle_deg = self._angle_from_mouse_for_grab(mx, my)
                return

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
            return

        if event.type == pygame.MOUSEMOTION and self.dragging:
            mx, my = event.pos
            self.angle_deg = self._angle_from_mouse_for_grab(mx, my)

    def update(self, dt: float) -> None:
        super().update(dt)

        rad = math.radians(self.angle_deg)
        a = self.g_eff * math.sin(rad)

        self.vel += a * dt
        damp = max(0.0, 1.0 - self.damping * dt)
        self.vel *= damp

        self.pos += self.vel * dt

        if self.pos <= 0.0:
            self.pos = 0.0
            self.vel = 0.0
        elif self.pos >= 1.0:
            self.pos = 1.0
            self.vel = 0.0

        new_value = int(round(self.pos * 100.0))
        if new_value != self.current_value:
            self.current_value = new_value
            self._volume_changed = True

    def render(self, screen: pygame.Surface) -> None:
        # 스피커(장식) 통일
        self.chrome.draw_speaker(screen, angle_deg=0.0)

        # 회전 막대(둥근 끝 유지)
        if self._bar_base is None:
            self._build_bar_surface()

        rotated = pygame.transform.rotozoom(self._bar_base, -self.angle_deg, 1.0)
        r = rotated.get_rect(center=(int(self.center.x), int(self.center.y)))
        screen.blit(rotated, r.topleft)

        # 볼
        bp = self._ball_world_pos()
        pygame.draw.circle(screen, (245, 245, 245), (int(bp.x), int(bp.y)), self.ball_radius)
        pygame.draw.circle(screen, (140, 140, 150), (int(bp.x), int(bp.y)), self.ball_radius, 2)
