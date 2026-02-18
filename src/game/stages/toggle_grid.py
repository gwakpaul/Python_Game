from __future__ import annotations

import random
import pygame
from ..core.stage_base import Stage


def _clamp_int(x: int, lo: int, hi: int) -> int:
    return lo if x < lo else hi if x > hi else x


class ToggleGridStage(Stage):
    stage_id: str = "toggle_grid"

    def __init__(
        self,
        target: int,
        play_rect: pygame.Rect,
        hold_seconds: float = 0.5,
        clear_mode: str = "hold",
        initial_value: int = 50,
    ) -> None:
        super().__init__(target, hold_seconds=hold_seconds, clear_mode=clear_mode)

        self.play_rect = play_rect.copy()

        self.selected_value: int | None = int(max(0, min(100, initial_value)))
        self._volume_changed = True

        self.circle_r = 11
        self.label_gap = 8

        # 10줄 고정, 각 줄 9~11 랜덤
        self.row_counts: list[int] = []

        # (value, circle_center, label_pos, hit_rect)
        self.items: list[tuple[int, tuple[int, int], tuple[int, int], pygame.Rect]] = []
        self.mute_center: tuple[int, int] | None = None
        self.mute_label_pos: tuple[int, int] | None = None
        self.mute_hit_rect: pygame.Rect | None = None

        self._rebuild_layout()

    def supports_numeric_value(self) -> bool:
        return True

    def get_current_value(self) -> int:
        if self.selected_value is None:
            return -1
        return int(self.selected_value)

    def set_play_rect(self, play_rect: pygame.Rect) -> None:
        self.play_rect = play_rect.copy()
        self._rebuild_layout()

    def consume_volume_changed(self) -> bool:
        if self._volume_changed:
            self._volume_changed = False
            return True
        return False

    def _make_row_counts_9_10_11_sum_100(self) -> list[int]:
        counts = [10] * 10
        swaps = random.randint(8, 18)
        for _ in range(swaps):
            i = random.randrange(10)
            j = random.randrange(10)
            if i == j:
                continue
            if counts[i] < 11 and counts[j] > 9:
                counts[i] += 1
                counts[j] -= 1
        return counts

    def _rebuild_layout(self) -> None:
        self.items.clear()
        self.row_counts = self._make_row_counts_9_10_11_sum_100()

        pad_x = 56
        pad_top = 92
        pad_bottom = 72

        left = self.play_rect.left + pad_x
        right = self.play_rect.right - pad_x
        top = self.play_rect.top + pad_top
        bottom = self.play_rect.bottom - pad_bottom

        usable_w = max(1, right - left)
        usable_h = max(1, bottom - top)

        rows = len(self.row_counts)  # 10

        reserved_for_mute = 56
        available_for_rows = max(1, usable_h - reserved_for_mute)

        row_h = max(26, min(44, available_for_rows // rows))
        self.circle_r = 10 if row_h <= 28 else 11

        # "무질서" 파라미터: 과하면 UI 붕괴하므로 제한적으로만
        # - 줄별 step을 0.92~1.08로 흔들기
        # - 각 점을 +/- 10px 범위로 흔들기(단, step이 좁으면 감소)
        base_min_step = 52

        v = 1
        for r in range(rows):
            n = self.row_counts[r]  # 9/10/11
            cy = top + r * row_h + row_h // 2

            base_step = max(base_min_step, int(usable_w / max(1, n)))
            step_scale = random.uniform(0.92, 1.08)
            step = max(base_min_step, int(base_step * step_scale))

            row_w = step * n
            start_x = (left + right) // 2 - row_w // 2

            # step이 좁아지면 jitter도 자동 축소
            jitter_max = min(10, max(2, int(step * 0.18)))

            for c in range(n):
                if v > 100:
                    break

                # 기본 x + jitter
                cx = start_x + c * step + 16 + random.randint(-jitter_max, jitter_max)

                # 좌우 경계 클램프(라벨/원 고려)
                cx = _clamp_int(cx, left + 10, right - 10)

                label_x = cx + self.circle_r + self.label_gap
                label_y = cy - 12

                hit = pygame.Rect(cx - 18, cy - 16, step, 32)
                self.items.append((v, (cx, cy), (label_x, label_y), hit))
                v += 1

        # Mute: 맨 아래 단독 줄 중앙
        min_bottom_gap = 28
        mute_y = top + rows * row_h + 18
        max_mute_y = self.play_rect.bottom - min_bottom_gap
        mute_y = min(mute_y, max_mute_y)

        mute_cx = self.play_rect.centerx - 24
        mute_cy = mute_y

        self.mute_center = (mute_cx, mute_cy)
        self.mute_label_pos = (mute_cx + self.circle_r + self.label_gap, mute_cy - 12)
        self.mute_hit_rect = pygame.Rect(mute_cx - 22, mute_cy - 16, 180, 32)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if not self.play_rect.collidepoint(mx, my):
                return

            for value, _, _, hit in self.items:
                if hit.collidepoint(mx, my):
                    if self.selected_value != value:
                        self.selected_value = value
                        self._volume_changed = True
                    return

            if self.mute_hit_rect and self.mute_hit_rect.collidepoint(mx, my):
                if self.selected_value != 0:
                    self.selected_value = 0
                    self._volume_changed = True
                return

    def update(self, dt: float) -> None:
        super().update(dt)

    def render(self, screen: pygame.Surface) -> None:
        font = pygame.font.SysFont("malgungothic", 16) or pygame.font.SysFont(None, 16)

        for value, (cx, cy), (lx, ly), _ in self.items:
            selected = (self.selected_value == value)

            pygame.draw.circle(screen, (220, 220, 220), (cx, cy), self.circle_r, 2)
            if selected:
                pygame.draw.circle(screen, (220, 220, 220), (cx, cy), self.circle_r - 5)

            label = font.render(str(value), True, (220, 220, 220))
            screen.blit(label, (lx, ly))

        if self.mute_center and self.mute_label_pos:
            cx, cy = self.mute_center
            selected = (self.selected_value == 0)

            pygame.draw.circle(screen, (220, 220, 220), (cx, cy), self.circle_r, 2)
            if selected:
                pygame.draw.circle(screen, (220, 220, 220), (cx, cy), self.circle_r - 5)

            label = font.render("Mute", True, (220, 220, 220))
            screen.blit(label, self.mute_label_pos)
