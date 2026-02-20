from __future__ import annotations

import random
import pygame

from ..core.stage_base import Stage


def _clamp_int(x: int, lo: int, hi: int) -> int:
    return lo if x < lo else hi if x > hi else x


def _clamp_float(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


class _PipePair:
    def __init__(
        self,
        x: float,
        gap_y: float,
        gap_h: int,
        w: int,
        label_value: int,
        already_passed: bool = False,
    ) -> None:
        self.x = float(x)
        self.gap_y = float(gap_y)
        self.gap_h = int(gap_h)
        self.w = int(w)
        self.label_value = int(label_value)
        self.passed = bool(already_passed)

    def right(self) -> float:
        return self.x + self.w

    def center_x(self) -> float:
        return self.x + self.w * 0.5


class FlappyVolumeStage(Stage):
    stage_id: str = "flappy_volume"

    def __init__(
        self,
        target: int,
        play_rect: pygame.Rect,
        initial_value: int = 50,
        hold_seconds: float = 0.0,
        clear_mode: str = "hold",
        start_delay_seconds: float = 1.0,
    ) -> None:
        super().__init__(target, hold_seconds=hold_seconds, clear_mode=clear_mode)

        self.play_rect = play_rect.copy()

        # ---- game rect ----
        self.game_rect = pygame.Rect(0, 0, 10, 10)

        # ---- score(=volume) ----
        self.start_value = _clamp_int(int(initial_value), 0, 100)
        self.current_value = int(self.start_value)
        self._value_changed = True

        # ---- death flag ----
        self._missed = False

        # ---- start delay ----
        self.start_delay_seconds = float(start_delay_seconds)
        self._wait_t = self.start_delay_seconds

        # ---- Bird (white ball) ----
        self.bird_r = 12
        self.bird_pos = pygame.Vector2(0, 0)
        self.bird_vel = pygame.Vector2(0, 0)

        # physics / difficulty
        self.gravity = 1900.0
        self.jump_vy = -442.0
        self.max_fall_vy = 900.0

        # ---- Pipes ----
        self.pipe_w = 72
        self.pipe_speed = 320.0

        # spacing
        self.pipe_spacing_px = 260
        self.spawn_ahead_px = 80

        self.pipes: list[_PipePair] = []
        self._next_label = self.start_value + 1

        # gap bounds
        self._min_gap_y = 0.0
        self._max_gap_y = 0.0

        # cap visuals
        self._cap_h = 12

        # ---- signboard(panel) safety sizing ----
        self._panel_font_size = 18
        self._panel_pad_y = 6
        self._panel_inner_margin = 10
        self._cap_to_panel_gap = 10
        self._panel_bottom_pad = 12
        self._panel_extra_bottom = int(round(self._panel_bottom_pad * 1.5))

        self._min_top_pipe_h = 80
        self._min_bottom_pipe_h = 70

        # ---- non-monotone gap generator state ----
        self._gap_center = 0.0
        self._gap_dir = random.choice([-1.0, 1.0])
        self._gap_step_base = 0.0

        # gap height (폭) : 고정값으로 운영
        self.pipe_gap_h_base = 150

        self._rebuild_layout()
        self._reset_world()

    def set_play_rect(self, play_rect: pygame.Rect) -> None:
        self.play_rect = play_rect.copy()
        self._rebuild_layout()
        self._reset_world()

    def _rebuild_layout(self) -> None:
        max_w = int(self.play_rect.width * 0.75)
        max_h = int(self.play_rect.height * 0.75)
        side = int(min(max_w, max_h))
        side = max(360, side)

        self.game_rect.size = (side, side)
        self.game_rect.center = (self.play_rect.centerx, self.play_rect.centery + 10)

        self.bird_vel = pygame.Vector2(0, 0)

        # 기둥 폭
        self.pipe_w = max(54, int(self.game_rect.width * 0.145))

        # ---- 통과 틈새 폭을 기존 대비 3/4로 줄임 ----
        base_gap = max(128, int(self.game_rect.height * 0.37))
        base_gap = int(round(base_gap * 0.75 * 1.2))
        base_gap = max(int(self.game_rect.height * 0.20), base_gap)
        self.pipe_gap_h_base = base_gap

        # 공 크기(원복)
        self.bird_r = max(10, int(self.game_rect.width * 0.028))

        # cap 높이
        self._cap_h = max(10, int(self.game_rect.height * 0.045))

        # ---- 표지판 기반 최소 기둥 길이 계산 ----
        panel_h = int(self._panel_font_size + 2 * self._panel_pad_y)

        self._min_top_pipe_h = (
            self._panel_inner_margin
            + panel_h
            + self._cap_to_panel_gap
            + self._cap_h
            + self._panel_extra_bottom
        )

        self._min_bottom_pipe_h = (
            self._panel_inner_margin
            + max(0, panel_h // 2)
            + self._cap_h
            + self._panel_extra_bottom
        )

        # gap_y 가능 범위 (폭은 pipe_gap_h_base 기준)
        margin = 34
        min_gap_y = float(self.game_rect.top + margin + self._min_top_pipe_h)
        max_gap_y = float(self.game_rect.bottom - margin - self.pipe_gap_h_base - self._min_bottom_pipe_h)

        if max_gap_y <= min_gap_y:
            mid = float(self.game_rect.centery - self.pipe_gap_h_base * 0.5)
            self._min_gap_y = mid
            self._max_gap_y = mid
        else:
            self._min_gap_y = min_gap_y
            self._max_gap_y = max_gap_y

        # ---- 변주 범위를 기존 대비 1.5~2배로 확대 ----
        gap_range = max(0.0, (self._max_gap_y - self._min_gap_y))
        self._gap_step_base = max(24.0, gap_range * 0.90)

        self.spawn_ahead_px = max(60, int(self.game_rect.width * 0.18))

    def _reset_world(self) -> None:
        self.current_value = int(self.start_value)
        self._value_changed = True

        self._missed = False
        self._cleared = False

        self._wait_t = self.start_delay_seconds

        self.bird_vel = pygame.Vector2(0, 0)

        self.pipes.clear()

        # gap generator init
        if self._max_gap_y > self._min_gap_y:
            self._gap_center = random.uniform(self._min_gap_y, self._max_gap_y)
        else:
            self._gap_center = self._min_gap_y
        self._gap_dir = random.choice([-1.0, 1.0])

        # ---- 시작 화면 배치 ----
        # (프레임) (여유) |N| (공) |N+1| (여유) (프레임)

        left_margin = int(self.game_rect.width * 0.14)
        right_margin = int(self.game_rect.width * 0.14)

        # N
        start_x = float(self.game_rect.left + left_margin)
        # N+1
        first_x = float(self.game_rect.right - right_margin - self.pipe_w)

        # spacing 확정
        spacing = int(round(first_x - start_x))
        spacing_min = int(self.game_rect.width * 0.42)
        spacing = max(spacing_min, spacing)
        self.pipe_spacing_px = spacing

        desired_first_x = start_x + float(spacing)
        if first_x < desired_first_x:
            dx = desired_first_x - first_x
            start_x += dx
            first_x += dx

        max_first_x = float(self.game_rect.right - right_margin - self.pipe_w)
        if first_x > max_first_x:
            dx = max_first_x - first_x
            start_x += dx
            first_x += dx

        min_start_x = float(self.game_rect.left + left_margin)
        if start_x < min_start_x:
            dx = min_start_x - start_x
            start_x += dx
            first_x += dx

        # 공 시작 위치: 두 기둥 사이 1/3 지점
        left_edge = start_x + float(self.pipe_w)
        right_edge = first_x
        one_third_x = left_edge + (right_edge - left_edge) * (1.0 / 3.0)

        self.bird_pos = pygame.Vector2(
            _clamp_float(one_third_x, self.game_rect.left + self.bird_r + 8, self.game_rect.right - self.bird_r - 8),
            float(self.game_rect.centery),
        )

        # 파이프 생성 (gap_h 고정, gap_y만 변주)
        gh = int(self.pipe_gap_h_base)

        # N: passed=True
        self.pipes.append(
            _PipePair(
                x=start_x,
                gap_y=self._next_gap_y(gh),
                gap_h=gh,
                w=self.pipe_w,
                label_value=self.start_value,
                already_passed=True,
            )
        )

        # N+1
        self.pipes.append(
            _PipePair(
                x=first_x,
                gap_y=self._next_gap_y(gh),
                gap_h=gh,
                w=self.pipe_w,
                label_value=self.start_value + 1,
                already_passed=False,
            )
        )

        # N+2 (동일 spacing)
        second_x = first_x + float(self.pipe_spacing_px)
        self.pipes.append(
            _PipePair(
                x=second_x,
                gap_y=self._next_gap_y(gh),
                gap_h=gh,
                w=self.pipe_w,
                label_value=self.start_value + 2,
                already_passed=False,
            )
        )

        self._next_label = self.start_value + 3

    # ---- StagePlayScene integration ----
    def supports_numeric_value(self) -> bool:
        return True

    def get_current_value(self) -> int:
        return int(self.current_value)

    def consume_volume_changed(self) -> bool:
        if self._value_changed:
            self._value_changed = False
            return True
        return False

    def consume_missed(self) -> bool:
        if self._missed:
            self._missed = False
            return True
        return False

    # ---- input ----
    def _do_jump(self) -> None:
        if self._wait_t > 0.0:
            return
        self.bird_vel.y = self.jump_vy

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._do_jump()
                return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._do_jump()
            return

    # ---- gap variation helpers (폭 고정, 위치만 랜덤) ----
    def _next_gap_center(self) -> float:
        if self._max_gap_y <= self._min_gap_y:
            return self._min_gap_y

        # 방향 반전
        if random.random() < 0.45:
            self._gap_dir *= -1.0

        # 기본 이동(더 큼)
        step = self._gap_step_base * random.uniform(0.95, 2.40) * self._gap_dir

        # 큰 점프(더 큼)
        if random.random() < 0.70:
            jump = (self._max_gap_y - self._min_gap_y) * random.uniform(0.65, 0.98) * random.choice([-1.0, 1.0])
            step += jump

        # 노이즈(더 큼)
        step += random.uniform(-self._gap_step_base * 0.95, self._gap_step_base * 0.95)

        self._gap_center = _clamp_float(self._gap_center + step, self._min_gap_y, self._max_gap_y)
        return self._gap_center

    def _next_gap_y(self, gap_h: int) -> float:
        margin = 34
        min_y = float(self.game_rect.top + margin + self._min_top_pipe_h)
        max_y = float(self.game_rect.bottom - margin - float(gap_h) - self._min_bottom_pipe_h)

        if max_y <= min_y:
            return float(self.game_rect.centery - gap_h * 0.5)

        c = self._next_gap_center()
        return float(_clamp_float(c, min_y, max_y))

    def _spawn_pipe_pair(self) -> None:
        if not self.pipes:
            base_x = float(self.game_rect.right + self.spawn_ahead_px)
        else:
            base_x = float(max(p.x for p in self.pipes) + self.pipe_spacing_px)

        x = base_x

        gap_h = int(self.pipe_gap_h_base)
        gap_y = self._next_gap_y(gap_h)

        label = int(self._next_label)
        self._next_label += 1

        self.pipes.append(
            _PipePair(
                x=x,
                gap_y=gap_y,
                gap_h=gap_h,
                w=self.pipe_w,
                label_value=label,
                already_passed=False,
            )
        )

    def _pipe_rects(self, p: _PipePair) -> tuple[pygame.Rect, pygame.Rect]:
        top_h = int(p.gap_y - self.game_rect.top)
        top_rect = pygame.Rect(int(p.x), self.game_rect.top, p.w, max(0, top_h))

        bot_y = int(p.gap_y + p.gap_h)
        bot_h = int(self.game_rect.bottom - bot_y)
        bot_rect = pygame.Rect(int(p.x), bot_y, p.w, max(0, bot_h))

        return top_rect, bot_rect

    def _bird_rect(self) -> pygame.Rect:
        return pygame.Rect(
            int(self.bird_pos.x - self.bird_r),
            int(self.bird_pos.y - self.bird_r),
            self.bird_r * 2,
            self.bird_r * 2,
        )

    def _die_and_finalize(self, force_fail: bool = False) -> None:
        """
        요구 조건:
        - 목표가 N이면 N 기둥을 넘고, N+1 기둥을 넘기 전에 죽으면 클리어.
        구현:
        - 죽는 순간 current_value == target 이면 cleared
        - cleared인 경우 missed를 올리지 않는다(StagePlayScene이 실패 처리로 먼저 빠지는 것 방지)
        - current_value가 target을 넘어서는 순간(=N+1 통과)은 즉시 fail 처리
        """
        if force_fail:
            self._cleared = False
            self._missed = True
            return

        if int(self.current_value) == int(self.get_target_value()):
            self._cleared = True
            self._missed = False
        else:
            self._cleared = False
            self._missed = True

    def update(self, dt: float) -> None:
        # 클리어/실패 처리 후에는 더 업데이트하지 않는다.
        if self._cleared or self._missed:
            return

        if self._wait_t > 0.0:
            self._wait_t -= dt
            if self._wait_t < 0.0:
                self._wait_t = 0.0
            return

        # bird physics
        self.bird_vel.y += self.gravity * dt
        if self.bird_vel.y > self.max_fall_vy:
            self.bird_vel.y = self.max_fall_vy
        self.bird_pos.y += self.bird_vel.y * dt

        # ceiling/floor -> death
        if self.bird_pos.y - self.bird_r <= self.game_rect.top:
            self.bird_pos.y = float(self.game_rect.top + self.bird_r)
            self._die_and_finalize()
            return
        if self.bird_pos.y + self.bird_r >= self.game_rect.bottom:
            self.bird_pos.y = float(self.game_rect.bottom - self.bird_r)
            self._die_and_finalize()
            return

        # pipes move
        for p in self.pipes:
            p.x -= self.pipe_speed * dt

        # remove old
        while self.pipes and self.pipes[0].right() < (self.game_rect.left - 60):
            self.pipes.pop(0)

        # spawn
        if self.pipes:
            rightmost = max(p.x for p in self.pipes)
            if rightmost <= float(self.game_rect.right + self.spawn_ahead_px):
                self._spawn_pipe_pair()

        # collision & scoring
        b = self._bird_rect()

        for p in self.pipes:
            top_rect, bot_rect = self._pipe_rects(p)

            if top_rect.height > 0 and b.colliderect(top_rect):
                self._die_and_finalize()
                return
            if bot_rect.height > 0 and b.colliderect(bot_rect):
                self._die_and_finalize()
                return

            if (not p.passed) and (self.bird_pos.x > p.center_x()):
                p.passed = True

                # 통과하면 current_value가 1 증가
                if self.current_value < 100:
                    self.current_value += 1
                    self._value_changed = True

                # 목표를 넘어섰다면(= N+1을 넘어버림) 즉시 실패 처리
                if int(self.current_value) > int(self.get_target_value()):
                    self._die_and_finalize(force_fail=True)
                    return

    # ---- rendering helpers ----
    def _draw_pipe(self, screen: pygame.Surface, rect: pygame.Rect, cap_side: str) -> None:
        if rect.width <= 0 or rect.height <= 0:
            return

        base = (60, 170, 70)
        dark = (35, 110, 45)
        border = (20, 40, 24)

        pygame.draw.rect(screen, base, rect)
        pygame.draw.rect(screen, border, rect, 2)

        stripe_w = max(6, rect.width // 6)
        stripe = pygame.Rect(rect.centerx - stripe_w // 2, rect.top + 2, stripe_w, rect.height - 4)
        pygame.draw.rect(screen, dark, stripe)

        cap_h = min(self._cap_h, rect.height)
        if cap_h <= 0:
            return

        if cap_side == "bottom":
            cap = pygame.Rect(rect.left - 6, rect.bottom - cap_h, rect.width + 12, cap_h)
        else:
            cap = pygame.Rect(rect.left - 6, rect.top, rect.width + 12, cap_h)

        pygame.draw.rect(screen, (70, 190, 80), cap)
        pygame.draw.rect(screen, border, cap, 2)

    def _draw_label_on_top_pipe(self, screen: pygame.Surface, font: pygame.font.Font, p: _PipePair) -> None:
        top_rect, _ = self._pipe_rects(p)
        if top_rect.height <= 0:
            return

        text = str(int(p.label_value))
        surf = font.render(text, True, (20, 20, 24))

        # panel 크기(고정)
        panel_w = surf.get_width() + 20
        panel_h = surf.get_height() + self._panel_pad_y * 2

        pad = self._panel_bottom_pad
        inner_margin = self._panel_inner_margin

        # 기본 y: 갭 근처(bottom)로 붙이되 위로 밀리면 top쪽으로 클램프
        desired_y = top_rect.bottom - panel_h - pad
        desired_y = max(top_rect.top + inner_margin, desired_y)

        panel = pygame.Rect(0, 0, panel_w, panel_h)

        # ---- (요구사항 1) 중앙 정렬 우선 ----
        panel.centerx = top_rect.centerx
        panel.top = desired_y

        # 좌우 경계 내로 클램프 (필요할 때만 이동)
        left_limit = top_rect.left + inner_margin
        right_limit = top_rect.right - inner_margin
        if panel.left < left_limit:
            panel.left = left_limit
        if panel.right > right_limit:
            panel.right = right_limit

        # 캡이 bottom 쪽에 있으므로 panel.bottom이 cap 시작보다 위로 충분히 떨어지게
        cap_h = min(self._cap_h, top_rect.height)
        cap_top = top_rect.bottom - cap_h
        min_panel_bottom = cap_top - self._cap_to_panel_gap
        if panel.bottom > min_panel_bottom:
            panel.bottom = min_panel_bottom

        # 마지막 안전 클램프
        if panel.height < 8:
            return
        if panel.top < top_rect.top + inner_margin:
            panel.top = top_rect.top + inner_margin

        # 텍스트 중앙
        tx = panel.centerx - surf.get_width() // 2
        ty = panel.centery - surf.get_height() // 2

        pygame.draw.rect(screen, (235, 235, 240), panel, border_radius=6)
        pygame.draw.rect(screen, (40, 40, 50), panel, width=2, border_radius=6)
        screen.blit(surf, (tx, ty))

    def render(self, screen: pygame.Surface) -> None:
        pygame.draw.rect(screen, (22, 22, 26), self.game_rect)
        pygame.draw.rect(screen, (90, 90, 105), self.game_rect, 2)

        prev_clip = screen.get_clip()
        screen.set_clip(self.game_rect)

        font = pygame.font.SysFont("malgungothic", self._panel_font_size) or pygame.font.SysFont(
            None, self._panel_font_size
        )

        for p in self.pipes:
            top_rect, bot_rect = self._pipe_rects(p)

            self._draw_pipe(screen, top_rect, cap_side="bottom")
            self._draw_pipe(screen, bot_rect, cap_side="top")

            self._draw_label_on_top_pipe(screen, font, p)

        pygame.draw.circle(
            screen,
            (245, 245, 245),
            (int(self.bird_pos.x), int(self.bird_pos.y)),
            self.bird_r,
        )
        pygame.draw.circle(
            screen,
            (40, 40, 50),
            (int(self.bird_pos.x), int(self.bird_pos.y)),
            self.bird_r,
            2,
        )

        screen.set_clip(prev_clip)