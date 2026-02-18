from __future__ import annotations

import math
import pygame

from ..core.stage_base import Stage
from ..ui.slider_chrome import SliderChrome


def _clamp_int(x: int, lo: int, hi: int) -> int:
    return lo if x < lo else hi if x > hi else x


class ScratchBarStage(Stage):
    stage_id: str = "scratch_bar"

    def __init__(
        self,
        target: int,
        play_rect: pygame.Rect,
        initial_value: int = 0,
        hold_seconds: float = 0.5,
        clear_mode: str = "hold",
    ) -> None:
        super().__init__(target, hold_seconds=hold_seconds, clear_mode=clear_mode)

        self.play_rect = play_rect.copy()
        self.chrome = SliderChrome()

        # 두께 1.3배 느낌 (14 -> 18)
        self.slider_rect = pygame.Rect(0, 0, 600, 18)

        # 테두리 안쪽만 칠하기
        self.inner_pad = max(2, int(self.chrome.bar_border_width))
        self.inner_rect = pygame.Rect(0, 0, 1, 1)

        self.scratch_surf: pygame.Surface | None = None

        # 좌클릭=그리기, 우클릭=지우기
        self.dragging = False
        self.erasing = False
        self._last_local: tuple[int, int] | None = None

        # 선 두께: 기존 10의 2/3 수준
        self.brush_px = 5

        # 면적 계산(중복 칠해도 변화 없음, 지우면 제거)
        self.cell_w = 6
        self.cell_h = 3
        self._covered: set[int] = set()
        self._cell_cols = 1
        self._cell_rows = 1
        self._total_cells = 1

        self.current_value = _clamp_int(int(initial_value), 0, 100)
        self._volume_changed = True

        self._rebuild_layout()

    def set_play_rect(self, play_rect: pygame.Rect) -> None:
        self.play_rect = play_rect.copy()
        self._rebuild_layout()

    def _rebuild_layout(self) -> None:
        self.chrome.layout_speaker_next_to_slider(self.play_rect, self.slider_rect)

        self.inner_rect = self.slider_rect.inflate(-2 * self.inner_pad, -2 * self.inner_pad)
        if self.inner_rect.width < 1:
            self.inner_rect.width = 1
        if self.inner_rect.height < 1:
            self.inner_rect.height = 1

        self.scratch_surf = pygame.Surface(self.inner_rect.size, pygame.SRCALPHA)

        w, h = self.inner_rect.size
        self._cell_cols = max(1, w // self.cell_w)
        self._cell_rows = max(1, h // self.cell_h)
        self._total_cells = self._cell_cols * self._cell_rows

        self._covered.clear()
        self.current_value = 0
        self._volume_changed = True

        self.dragging = False
        self.erasing = False
        self._last_local = None

    def supports_numeric_value(self) -> bool:
        return True

    def get_current_value(self) -> int:
        return int(self.current_value)

    def consume_volume_changed(self) -> bool:
        if self._volume_changed:
            self._volume_changed = False
            return True
        return False

    def _local_from_mouse(self, mx: int, my: int) -> tuple[int, int]:
        lx = mx - self.inner_rect.left
        ly = my - self.inner_rect.top
        lx = _clamp_int(lx, 0, self.inner_rect.width - 1)
        ly = _clamp_int(ly, 0, self.inner_rect.height - 1)
        return lx, ly

    def _cell_index(self, cx: int, cy: int) -> int:
        return cy * self._cell_cols + cx

    def _mark_cells_around(self, lx: int, ly: int) -> set[int]:
        r = self.brush_px * 0.5
        r2 = r * r

        cc = lx // self.cell_w
        rr = ly // self.cell_h
        rad_c = int(math.ceil(r / float(self.cell_w))) + 1
        rad_r = int(math.ceil(r / float(self.cell_h))) + 1

        x0 = max(0, cc - rad_c)
        x1 = min(self._cell_cols - 1, cc + rad_c)
        y0 = max(0, rr - rad_r)
        y1 = min(self._cell_rows - 1, rr + rad_r)

        affected: set[int] = set()
        for cy in range(y0, y1 + 1):
            for cx in range(x0, x1 + 1):
                center_x = cx * self.cell_w + (self.cell_w * 0.5)
                center_y = cy * self.cell_h + (self.cell_h * 0.5)
                dx = center_x - lx
                dy = center_y - ly
                if (dx * dx + dy * dy) <= r2:
                    affected.add(self._cell_index(cx, cy))
        return affected

    def _apply_coverage(self, affected: set[int], erase: bool) -> bool:
        if not affected:
            return False

        if erase:
            before = len(self._covered)
            self._covered.difference_update(affected)
            return len(self._covered) != before

        before = len(self._covered)
        self._covered.update(affected)
        return len(self._covered) != before

    def _update_value_from_coverage(self) -> None:
        ratio = len(self._covered) / float(self._total_cells) if self._total_cells > 0 else 0.0
        new_value = int(round(ratio * 100.0))
        new_value = _clamp_int(new_value, 0, 100)
        if new_value != self.current_value:
            self.current_value = new_value
            self._volume_changed = True

    def _erase_shape_minblend(self, draw_fn) -> None:
        """
        scratch_surf에서 특정 영역을 '투명'으로 만들기 위한 공용 루틴.
        - temp를 (255,255,255,255)로 채우고
        - 지울 영역만 (0,0,0,0)으로 그린 뒤
        - BLEND_RGBA_MIN으로 합성하면 해당 영역 alpha가 0으로 떨어짐
        """
        if self.scratch_surf is None:
            return

        temp = pygame.Surface(self.scratch_surf.get_size(), pygame.SRCALPHA)
        temp.fill((255, 255, 255, 255))
        draw_fn(temp)  # 지울 도형만 0 alpha로 그리기
        self.scratch_surf.blit(temp, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

    def _draw_line(self, x0: int, y0: int, x1: int, y1: int, erase: bool) -> None:
        if self.scratch_surf is None:
            return

        if erase:
            def _fn(s: pygame.Surface) -> None:
                pygame.draw.line(s, (0, 0, 0, 0), (x0, y0), (x1, y1), self.brush_px)
            self._erase_shape_minblend(_fn)
        else:
            pygame.draw.line(self.scratch_surf, (0, 0, 0, 255), (x0, y0), (x1, y1), self.brush_px)

    def _draw_dot(self, x: int, y: int, erase: bool) -> None:
        if self.scratch_surf is None:
            return
        r = max(1, self.brush_px // 2)

        if erase:
            def _fn(s: pygame.Surface) -> None:
                pygame.draw.circle(s, (0, 0, 0, 0), (x, y), r)
            self._erase_shape_minblend(_fn)
        else:
            pygame.draw.circle(self.scratch_surf, (0, 0, 0, 255), (x, y), r)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            if not self.inner_rect.collidepoint(mx, my):
                return

            # 좌클릭(1)=그리기, 우클릭(3)=지우기
            if event.button not in (1, 3):
                return

            self.dragging = True
            self.erasing = (event.button == 3)

            lx, ly = self._local_from_mouse(mx, my)
            self._last_local = (lx, ly)

            # 점 1회 반영
            self._draw_dot(lx, ly, erase=self.erasing)

            changed = self._apply_coverage(self._mark_cells_around(lx, ly), erase=self.erasing)
            if changed:
                self._update_value_from_coverage()
            return

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button in (1, 3):
                self.dragging = False
                self.erasing = False
                self._last_local = None
            return

        if event.type == pygame.MOUSEMOTION and self.dragging:
            mx, my = event.pos
            lx, ly = self._local_from_mouse(mx, my)

            if self._last_local is None:
                self._last_local = (lx, ly)
                return

            x0, y0 = self._last_local
            x1, y1 = lx, ly

            self._draw_line(x0, y0, x1, y1, erase=self.erasing)

            dx = x1 - x0
            dy = y1 - y0
            dist = math.hypot(dx, dy)
            step = 3.0
            n = max(1, int(dist / step))

            changed = False
            for i in range(n + 1):
                t = i / float(n)
                sx = int(round(x0 + dx * t))
                sy = int(round(y0 + dy * t))
                if self._apply_coverage(self._mark_cells_around(sx, sy), erase=self.erasing):
                    changed = True

            if changed:
                self._update_value_from_coverage()

            self._last_local = (x1, y1)

    def update(self, dt: float) -> None:
        super().update(dt)

    def render(self, screen: pygame.Surface) -> None:
        self.chrome.draw_speaker(screen, angle_deg=0.0)
        self.chrome.draw_slider_bar(screen, self.slider_rect)

        if self.scratch_surf is not None:
            prev = screen.get_clip()
            screen.set_clip(self.inner_rect)
            screen.blit(self.scratch_surf, self.inner_rect.topleft)
            screen.set_clip(prev)
