from __future__ import annotations

import math
import pygame

from ..core.stage_base import Stage
from ..ui.slider_chrome import SliderChrome


class CannonShotStage(Stage):
    stage_id: str = "cannon_shot"

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

        self.current_value = int(max(0, min(100, initial_value)))
        self._volume_changed = True

        # ---- 공통 UI(스피커/배치 통일) ----
        self.chrome = SliderChrome()
        self.slider_rect = pygame.Rect(0, 0, 600, 14)
        self.knob_radius = 9

        # ---- charge / aim ----
        self.aiming = False
        self.charge_t = 0.0
        self.charge_max = 1.10  # seconds

        # 차징에 따라 0 -> 위로 최대 -70도
        self.angle_base_deg = 0.0
        self.angle_max_up_deg = -70.0

        # 파워(너가 튜닝한 체감 유지)
        self.power_min = 370.0
        self.power_max = 1050.0

        # projectile
        self.flying = False
        self.ball_pos = pygame.Vector2(0, 0)
        self.ball_vel = pygame.Vector2(0, 0)
        self.ball_radius = 7
        self.gravity = 1250.0

        self._landed_this_shot = False

        # gauge layout
        self.gauge_w = 114
        self.gauge_h = 10
        self.gauge_gap_below_speaker = 10

        self._rebuild_layout()

    def set_play_rect(self, play_rect: pygame.Rect) -> None:
        self.play_rect = play_rect.copy()
        self._rebuild_layout()

    def _rebuild_layout(self) -> None:
        # 3스테이지 기준 레이아웃을 공통 chrome으로 고정
        self.chrome.layout_speaker_next_to_slider(self.play_rect, self.slider_rect)

        # idle 상태에서 공 위치를 스피커 중앙으로
        if not self.flying and not self.aiming:
            self.ball_pos = pygame.Vector2(self.chrome.speaker_rect.centerx, self.chrome.speaker_rect.centery)

    def supports_numeric_value(self) -> bool:
        return True

    def get_current_value(self) -> int:
        return int(self.current_value)

    def consume_volume_changed(self) -> bool:
        if self._volume_changed:
            self._volume_changed = False
            return True
        return False

    def _charge_ratio(self) -> float:
        if self.charge_max <= 0:
            return 0.0
        return max(0.0, min(1.0, self.charge_t / self.charge_max))

    def _angle_and_power(self) -> tuple[float, float]:
        r = self._charge_ratio()
        angle = self.angle_base_deg + (self.angle_max_up_deg - self.angle_base_deg) * r
        power = self.power_min + (self.power_max - self.power_min) * r
        return angle, power

    def _launch(self) -> None:
        angle_deg, power = self._angle_and_power()
        rad = math.radians(angle_deg)

        self.flying = True
        self._landed_this_shot = False

        sp = self.chrome.speaker_rect
        start_x = float(sp.right + 6)
        start_y = float(sp.centery - 2)
        self.ball_pos = pygame.Vector2(start_x, start_y)

        vx = math.cos(rad) * power
        vy = math.sin(rad) * power
        self.ball_vel = pygame.Vector2(vx, vy)

    def _compute_volume_from_x(self, x: float) -> int:
        left = float(self.slider_rect.left)
        right = float(self.slider_rect.right)
        if right <= left:
            return 0
        ratio = (x - left) / (right - left)
        ratio = max(0.0, min(1.0, ratio))
        return int(round(ratio * 100.0))

    def _knob_pos(self) -> tuple[int, int]:
        x = self.slider_rect.left + (self.current_value / 100.0) * self.slider_rect.width
        y = self.slider_rect.centery
        return int(x), int(y)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self.chrome.speaker_rect.collidepoint(mx, my) and (not self.flying):
                self.aiming = True
                self.charge_t = 0.0
                return

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.aiming:
                self.aiming = False
                self._launch()
                return

    def update(self, dt: float) -> None:
        super().update(dt)

        if self.aiming:
            self.charge_t += dt
            if self.charge_t > self.charge_max:
                self.charge_t = self.charge_max

        if self.flying:
            self.ball_vel.y += self.gravity * dt
            self.ball_pos += self.ball_vel * dt

            # 착지: 슬라이더 바와 충돌(하강 중)
            if (not self._landed_this_shot) and (self.ball_vel.y > 0):
                bar_top = float(self.slider_rect.top)
                bar_bottom = float(self.slider_rect.bottom)

                if (self.ball_pos.y + self.ball_radius) >= bar_top and (self.ball_pos.y - self.ball_radius) <= bar_bottom:
                    if self.slider_rect.left <= int(self.ball_pos.x) <= self.slider_rect.right:
                        self._landed_this_shot = True
                        self.flying = False

                        new_value = self._compute_volume_from_x(self.ball_pos.x)
                        if new_value != self.current_value:
                            self.current_value = new_value
                            self._volume_changed = True

                        self.ball_vel = pygame.Vector2(0, 0)
                        return

            # 프레임 밖으로 나가면 miss 처리 후 복귀
            if (
                (self.ball_pos.x < self.play_rect.left - 200)
                or (self.ball_pos.x > self.play_rect.right + 200)
                or (self.ball_pos.y > self.play_rect.bottom + 300)
            ):
                self.flying = False
                self._landed_this_shot = False
                self.ball_vel = pygame.Vector2(0, 0)
                self.ball_pos = pygame.Vector2(self.chrome.speaker_rect.centerx, self.chrome.speaker_rect.centery)

    def render(self, screen: pygame.Surface) -> None:
        # 스피커: aiming 중에는 회전(통일된 스피커 룩)
        angle_deg, _ = self._angle_and_power()
        draw_angle = angle_deg if self.aiming else 0.0
        self.chrome.draw_speaker(screen, angle_deg=draw_angle)

        # 슬라이더 바(통일 룩)
        self.chrome.draw_slider_bar(screen, self.slider_rect)

        # 노브: aiming/비행 중에는 숨김
        if (not self.aiming) and (not self.flying):
            kx, ky = self._knob_pos()
            pygame.draw.circle(screen, (245, 245, 245), (kx, ky), self.knob_radius)
            pygame.draw.circle(screen, (140, 140, 150), (kx, ky), self.knob_radius, 2)

        # 비행 탄환
        if self.flying:
            pygame.draw.circle(
                screen,
                (235, 235, 235),
                (int(self.ball_pos.x), int(self.ball_pos.y)),
                self.ball_radius,
            )

        # 게이지: 스피커 아래
        if self.aiming:
            self._draw_gauge_below_speaker(screen)

    def _draw_gauge_below_speaker(self, screen: pygame.Surface) -> None:
        sp = self.chrome.speaker_rect
        bx = sp.centerx - self.gauge_w // 2
        by = sp.bottom + self.gauge_gap_below_speaker

        max_y = self.play_rect.bottom - 40
        if by > max_y:
            by = max_y

        bg = pygame.Rect(bx, by, self.gauge_w, self.gauge_h)
        pygame.draw.rect(screen, (70, 70, 80), bg, border_radius=6)

        r = self._charge_ratio()
        fg = pygame.Rect(bx, by, int(self.gauge_w * r), self.gauge_h)
        pygame.draw.rect(screen, (200, 200, 200), fg, border_radius=6)
