from __future__ import annotations

import random
import pygame

from ..core.stage_base import Stage


def _clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


class PongBounceStage(Stage):
    stage_id: str = "pong_bounce"

    def __init__(
        self,
        target: int,
        play_rect: pygame.Rect,
        initial_value: int = 50,  # 다른 스테이지와 시그니처를 맞추기 위해 남겨둠(여기선 사용 안함)
        hold_seconds: float = 0.5,
        clear_mode: str = "hold",
        speed_scale: float = 0.70,  # 공 속도 스케일(더 줄이고 싶으면 0.65 등)
        start_delay_seconds: float = 1.0,  # 진입/재시작 후 공 출발 지연
    ) -> None:
        super().__init__(target, hold_seconds=hold_seconds, clear_mode=clear_mode)

        self.play_rect = play_rect.copy()

        # ---- 이 스테이지에서 "Current"는 점수(튕긴 횟수)로 정의 ----
        self.current_value = 0
        self._value_changed = True

        # 실패(공이 좌/우로 나감)
        self._missed = False

        # ---- game rect (작고, 가로가 살짝 더 긴 직사각형) ----
        self.game_rect = pygame.Rect(0, 0, 10, 10)

        # 패들/볼 파라미터
        self.paddle_w = 14
        self.paddle_h = 92

        self.ball_r = 8
        base_speed = 520.0
        self.ball_speed = base_speed * float(speed_scale)

        # 패들: y 공유(완전 연동), 조작은 마우스 Y 따라가기
        self.paddle_y = 0.0
        self.left_paddle = pygame.Rect(0, 0, self.paddle_w, self.paddle_h)
        self.right_paddle = pygame.Rect(0, 0, self.paddle_w, self.paddle_h)

        # 볼
        self.ball_pos = pygame.Vector2(0, 0)
        self.ball_vel = pygame.Vector2(0, 0)

        # 시작 딜레이
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

        # 재시작 시에도 1초 대기
        self._wait_t = self.start_delay_seconds

    # ---- StagePlayScene 연동 ----
    def supports_numeric_value(self) -> bool:
        # StagePlayScene 우상단 Current 표기에 사용됨
        return True

    def get_current_value(self) -> int:
        return int(self.current_value)

    def consume_volume_changed(self) -> bool:
        # 기존 이름과의 호환을 위해 유지(실제로는 "값 변경" 신호)
        if self._value_changed:
            self._value_changed = False
            return True
        return False

    def get_audio_volume_ratio(self) -> float:
        # 점수가 올라갈수록 BGM이 커지게 (0~1)
        return max(0.0, min(1.0, float(self.current_value) / 100.0))

    def consume_missed(self) -> bool:
        if self._missed:
            self._missed = False
            return True
        return False

    def _inc_score(self) -> None:
        # 2씩 증가 문제 해결: 1씩만 증가
        if self.current_value < 100:
            self.current_value += 1
            self._value_changed = True

    def _paddle_clamp_y(self, y: float) -> float:
        top_lim = float(self.game_rect.top + 18 + self.paddle_h * 0.5)
        bot_lim = float(self.game_rect.bottom - 18 - self.paddle_h * 0.5)
        return _clamp(y, top_lim, bot_lim)

    def handle_event(self, event: pygame.event.Event) -> None:
        # 드래그/키 입력 없음 (마우스 위치 추적은 update에서 처리)
        return

    def update(self, dt: float) -> None:
        super().update(dt)

        # ---- (요구사항 1) 플레이 영역 안에서만 입력 활성 ----
        mx, my = pygame.mouse.get_pos()
        if self.game_rect.collidepoint(mx, my):
            self.paddle_y = self._paddle_clamp_y(float(my))
            self.left_paddle.centery = int(self.paddle_y)
            self.right_paddle.centery = int(self.paddle_y)
        # game_rect 밖이면 패들 위치 고정(변경 없음)

        # 시작 대기 시간 동안은 공이 정지
        if self._wait_t > 0.0:
            self._wait_t -= dt
            if self._wait_t < 0.0:
                self._wait_t = 0.0
            return

        # 볼 이동
        self.ball_pos += self.ball_vel * dt

        # 위/아래 반사
        if self.ball_pos.y - self.ball_r <= self.game_rect.top + 10:
            self.ball_pos.y = self.game_rect.top + 10 + self.ball_r
            self.ball_vel.y *= -1
        elif self.ball_pos.y + self.ball_r >= self.game_rect.bottom - 10:
            self.ball_pos.y = self.game_rect.bottom - 10 - self.ball_r
            self.ball_vel.y *= -1

        # 좌/우: "나가는 연출" 없이 즉시 실패 처리
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

        # 패들 충돌
        if self.ball_vel.x < 0 and ball_rect.colliderect(self.left_paddle):
            self.ball_pos.x = self.left_paddle.right + self.ball_r + 1
            self.ball_vel.x *= -1
            self._inc_score()

            off = (self.ball_pos.y - self.left_paddle.centery) / (self.paddle_h * 0.5)
            self.ball_vel.y += float(off) * 120.0

        if self.ball_vel.x > 0 and ball_rect.colliderect(self.right_paddle):
            self.ball_pos.x = self.right_paddle.left - self.ball_r - 1
            self.ball_vel.x *= -1
            self._inc_score()

            off = (self.ball_pos.y - self.right_paddle.centery) / (self.paddle_h * 0.5)
            self.ball_vel.y += float(off) * 120.0

        # 속도 제한(너무 느려지거나 과하게 빨라지지 않도록)
        sp = self.ball_vel.length()
        if sp < self.ball_speed * 0.75:
            self.ball_vel = self.ball_vel.normalize() * (self.ball_speed * 0.75)
        elif sp > self.ball_speed * 1.20:
            self.ball_vel = self.ball_vel.normalize() * (self.ball_speed * 1.20)

    def render(self, screen: pygame.Surface) -> None:
        pygame.draw.rect(screen, (90, 90, 105), self.game_rect, 2, border_radius=8)

        # 중앙 점선
        cx = self.game_rect.centerx
        for y in range(self.game_rect.top + 16, self.game_rect.bottom - 16, 18):
            pygame.draw.rect(screen, (90, 90, 105), pygame.Rect(cx - 2, y, 4, 10))

        # 패들
        pygame.draw.rect(screen, (235, 235, 235), self.left_paddle, border_radius=6)
        pygame.draw.rect(screen, (235, 235, 235), self.right_paddle, border_radius=6)

        # 볼 (대기 중에도 보이게)
        pygame.draw.circle(
            screen,
            (235, 235, 235),
            (int(self.ball_pos.x), int(self.ball_pos.y)),
            self.ball_r,
        )
