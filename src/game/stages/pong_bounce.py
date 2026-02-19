from __future__ import annotations

import random
import pygame

from ..core.stage_base import Stage


def _clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else hi


def _clamp_int(x: int, lo: int, hi: int) -> int:
    return lo if x < lo else hi if x > hi else x


class PongBounceStage(Stage):
    stage_id: str = "pong_bounce"

    def __init__(
        self,
        target: int,
        play_rect: pygame.Rect,
        initial_value: int = 50,
        hold_seconds: float = 0.5,
        clear_mode: str = "hold",
        speed_scale: float = 0.70,
        start_delay_seconds: float = 1.0,
    ) -> None:
        super().__init__(target, hold_seconds=hold_seconds, clear_mode=clear_mode)

        self.play_rect = play_rect.copy()

        # ---- 이 스테이지에서 "Current"는 '현재 볼륨 값'으로 취급 ----
        self.current_value = _clamp_int(int(initial_value), 0, 100)
        self._value_changed = True

        self._missed = False

        self.game_rect = pygame.Rect(0, 0, 10, 10)

        self.paddle_w = 14
        self.paddle_h = 92

        self.ball_r = 8
        base_speed = 520.0
        self.ball_speed = base_speed * float(speed_scale)

        self.paddle_y = 0.0
        self.left_paddle = pygame.Rect(0, 0, self.paddle_w, self.paddle_h)
        self.right_paddle = pygame.Rect(0, 0, self.paddle_w, self.paddle_h)

        self.ball_pos = pygame.Vector2(0, 0)
        self.ball_vel = pygame.Vector2(0, 0)

        self.start_delay_seconds = float(start_delay_seconds)
        self._wait_t = self.start_delay_seconds

        self._rebuild_layout()
        self._reset_ball(direction=random.choice([-1, 1]))

    def set_play_rect(self, play_rect: pygame.Rect) -> None:
        self.play_rect = play_rect.copy()
        self._rebuild_layout()

    def _rebuild_layout(self) -> None:
        max_w = int(self.play_rect.width * 0.78)
        max_h = int(self.play_rect.height * 0.60)
        h = max_h
        w = int(h * 1.25)

        if w > max_w:
            w = max_w
            h = int(w / 1.25)

        w = max(420, w)
        h = max(240, h)

        self.game_rect.size = (w, h)
        self.game_rect.center = (self.play_rect.centerx, self.play_rect.centery + 20)

        pad_x = 26
        self.left_paddle.left = self.game_rect.left + pad_x
        self.right_paddle.right = self.game_rect.right - pad_x

        self.paddle_y = float(self.game_rect.centery)
        self.left_paddle.centery = int(self.paddle_y)
        self.right_paddle.centery = int(self.paddle_y)

        self.ball_pos = pygame.Vector2(self.game_rect.centerx, self.game_rect.centery)

    def _reset_ball(self, direction: int) -> None:
        self.ball_pos = pygame.Vector2(self.game_rect.centerx, self.game_rect.centery)

        vy = random.uniform(-0.55, 0.55)
        vx = float(direction)

        v = pygame.Vector2(vx, vy)
        if v.length_squared() == 0:
            v = pygame.Vector2(1, 0)
        v = v.normalize() * self.ball_speed
        self.ball_vel = v

        self._wait_t = self.start_delay_seconds

    def supports_numeric_value(self) -> bool:
        return True

    def get_current_value(self) -> int:
        return int(self.current_value)

    def consume_volume_changed(self) -> bool:
        if self._value_changed:
            self._value_changed = False
            return True
        return False

    def get_audio_volume_ratio(self) -> float:
        return max(0.0, min(1.0, float(self.current_value) / 100.0))

    def consume_missed(self) -> bool:
        if self._missed:
            self._missed = False
            return True
        return False

    def _inc_value_on_bounce(self) -> None:
        if self.current_value < 100:
            self.current_value += 1
            self._value_changed = True

    def _paddle_clamp_y(self, y: float) -> float:
        top_lim = float(self.game_rect.top + 18 + self.paddle_h * 0.5)
        bot_lim = float(self.game_rect.bottom - 18 - self.paddle_h * 0.5)
        return _clamp(y, top_lim, bot_lim)

    def handle_event(self, event: pygame.event.Event) -> None:
        return

    def update(self, dt: float) -> None:
        super().update(dt)

        mx, my = pygame.mouse.get_pos()
        if self.game_rect.collidepoint(mx, my):
            self.paddle_y = self._paddle_clamp_y(float(my))
            self.left_paddle.centery = int(self.paddle_y)
            self.right_paddle.centery = int(self.paddle_y)

        if self._wait_t > 0.0:
            self._wait_t -= dt
            if self._wait_t < 0.0:
                self._wait_t = 0.0
            return

        self.ball_pos += self.ball_vel * dt

        if self.ball_pos.y - self.ball_r <= self.game_rect.top + 10:
            self.ball_pos.y = self.game_rect.top + 10 + self.ball_r
            self.ball_vel.y *= -1
        elif self.ball_pos.y + self.ball_r >= self.game_rect.bottom - 10:
            self.ball_pos.y = self.game_rect.bottom - 10 - self.ball_r
            self.ball_vel.y *= -1

        if self.ball_pos.x - self.ball_r <= self.game_rect.left + 2:
            self._missed = True
            return
        if self.ball_pos.x + self.ball_r >= self.game_rect.right - 2:
            self._missed = True
            return

        ball_rect = pygame.Rect(
            int(self.ball_pos.x - self.ball_r),
            int(self.ball_pos.y - self.ball_r),
            self.ball_r * 2,
            self.ball_r * 2,
        )

        if self.ball_vel.x < 0 and ball_rect.colliderect(self.left_paddle):
            self.ball_pos.x = self.left_paddle.right + self.ball_r + 1
            self.ball_vel.x *= -1
            self._inc_value_on_bounce()

            off = (self.ball_pos.y - self.left_paddle.centery) / (self.paddle_h * 0.5)
            self.ball_vel.y += float(off) * 120.0

        if self.ball_vel.x > 0 and ball_rect.colliderect(self.right_paddle):
            self.ball_pos.x = self.right_paddle.left - self.ball_r - 1
            self.ball_vel.x *= -1
            self._inc_value_on_bounce()

            off = (self.ball_pos.y - self.right_paddle.centery) / (self.paddle_h * 0.5)
            self.ball_vel.y += float(off) * 120.0

        sp = self.ball_vel.length()
        if sp < self.ball_speed * 0.75:
            self.ball_vel = self.ball_vel.normalize() * (self.ball_speed * 0.75)
        elif sp > self.ball_speed * 1.20:
            self.ball_vel = self.ball_vel.normalize() * (self.ball_speed * 1.20)

    def render(self, screen: pygame.Surface) -> None:
        pygame.draw.rect(screen, (90, 90, 105), self.game_rect, 2, border_radius=8)

        cx = self.game_rect.centerx
        for y in range(self.game_rect.top + 16, self.game_rect.bottom - 16, 18):
            pygame.draw.rect(screen, (90, 90, 105), pygame.Rect(cx - 2, y, 4, 10))

        pygame.draw.rect(screen, (235, 235, 235), self.left_paddle, border_radius=6)
        pygame.draw.rect(screen, (235, 235, 235), self.right_paddle, border_radius=6)

        pygame.draw.circle(
            screen,
            (235, 235, 235),
            (int(self.ball_pos.x), int(self.ball_pos.y)),
            self.ball_r,
        )
