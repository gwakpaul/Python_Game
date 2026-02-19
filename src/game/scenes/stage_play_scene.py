from __future__ import annotations

import random
import pygame

from ..core.scene_base import Scene

from ..stages.slider_normal import SliderNormalStage
from ..stages.toggle_grid import ToggleGridStage
from ..stages.cannon_shot import CannonShotStage
from ..stages.tilt_slider import TiltSliderStage
from ..stages.scratch_bar import ScratchBarStage
from ..stages.pong_bounce import PongBounceStage
from ..stages.slide_random import SlideRandomStage, make_random_mapping_0_100
from ..stages.lever_crank import LeverCrankStage  # (추가) 8스테이지

from ..systems.persist import load_progress, save_progress, load_settings
from ..systems.stage_catalog import StageCatalog
from ..ui.widgets import Button, Toast
from ..ui.header import Header
from ..ui.modal_dialog import ModalDialog


def pick_target_within_range(initial_value: int, radius: int, min_distance: int = 0) -> int:
    """
    initial_value를 기준으로 [-radius, +radius] 범위 내에서 target을 선택.
    min_distance > 0이면 initial 근처(+-min_distance)는 피한다.
    """
    iv = int(initial_value)
    lo = max(0, iv - int(radius))
    hi = min(100, iv + int(radius))

    if min_distance > 0:
        ban_lo = max(0, iv - int(min_distance))
        ban_hi = min(100, iv + int(min_distance))
        candidates = [x for x in range(lo, hi + 1) if not (ban_lo <= x <= ban_hi)]
    else:
        candidates = list(range(lo, hi + 1))

    if candidates:
        return random.choice(candidates)

    return random.randint(lo, hi)


def _draw_speaker_icon(screen: pygame.Surface, center: tuple[int, int], scale: float = 1.0) -> None:
    cx, cy = center
    s = float(scale)

    fg = (235, 235, 235)

    body_w = int(9 * s)
    body_h = int(10 * s)
    body = pygame.Rect(cx - int(12 * s), cy - body_h // 2, body_w, body_h)
    pygame.draw.rect(screen, fg, body, border_radius=max(1, int(2 * s)))

    top = (body.right, body.top + int(1 * s))
    bot = (body.right, body.bottom - int(1 * s))
    out_top = (body.right + int(8 * s), cy - int(5 * s))
    out_bot = (body.right + int(8 * s), cy + int(5 * s))
    pygame.draw.polygon(screen, fg, [top, out_top, out_bot, bot])

    for r in [int(8 * s), int(12 * s)]:
        rect = pygame.Rect(cx + int(2 * s), cy - r, r * 2, r * 2)
        pygame.draw.arc(screen, fg, rect, -0.65, 0.65, width=max(1, int(2 * s)))


def _draw_vertical_volume_meter(
    screen: pygame.Surface,
    rect: pygame.Rect,
    value_0_100: int | None,
    font: pygame.font.Font,
) -> None:
    x, y, w, h = rect.x, rect.y, rect.w, rect.h

    num_h = 26
    speaker_h = 22
    gap = 6
    bar_h = h - num_h - speaker_h - gap * 2
    if bar_h < 10:
        bar_h = 10

    num_rect = pygame.Rect(x, y, w, num_h)
    bar_rect = pygame.Rect(x + w // 2 - 8, y + num_h + gap, 16, bar_h)
    speaker_center = (x + w // 2, y + num_h + gap + bar_h + gap + speaker_h // 2)

    pygame.draw.rect(screen, (120, 120, 120), num_rect, border_radius=4)
    pygame.draw.rect(screen, (60, 60, 70), num_rect, width=2, border_radius=4)

    if value_0_100 is None:
        txt = "N/A"
    else:
        v = max(0, min(100, int(value_0_100)))
        txt = str(v)

    base_surf = font.render(txt, True, (245, 245, 245))
    scale = 0.82
    tw = max(1, int(base_surf.get_width() * scale))
    th = max(1, int(base_surf.get_height() * scale))
    surf = pygame.transform.smoothscale(base_surf, (tw, th))
    screen.blit(surf, surf.get_rect(center=num_rect.center))

    pygame.draw.rect(screen, (160, 160, 160), bar_rect, border_radius=3)
    pygame.draw.rect(screen, (90, 90, 105), bar_rect, width=2, border_radius=3)

    if value_0_100 is not None:
        v = max(0, min(100, int(value_0_100)))
        fill_h = int(round((v / 100.0) * bar_rect.height))
        fill = pygame.Rect(bar_rect.left + 2, bar_rect.bottom - fill_h + 2, bar_rect.width - 4, fill_h - 4)
        if fill.height > 0:
            pygame.draw.rect(screen, (30, 200, 60), fill, border_radius=2)

    _draw_speaker_icon(screen, speaker_center, scale=0.95)


class StagePlayScene(Scene):
    def __init__(self, app, stage_number: int, stage_id: str, mode: str) -> None:
        super().__init__(app)

        self.stage_number = int(stage_number)
        self.stage_id = str(stage_id)
        self.mode = str(mode)  # "stage" or "challenge"

        self.catalog = StageCatalog.load()
        self.toast = Toast()

        self.btn_home = Button(pygame.Rect(20, 20, 120, 40), "Home")
        self.btn_stage = Button(pygame.Rect(150, 20, 120, 40), "Stage")
        self.btn_restart = Button(pygame.Rect(280, 20, 120, 40), "Restart")

        self.elapsed = 0.0
        self.fail_count = 0

        self.play_rect = pygame.Rect(0, 0, 860, 440)

        self.stage = None
        self._cleared_once = False

        self._modal: ModalDialog | None = None
        self._modal_left_action = None
        self._modal_right_action = None

        self.stage_time_limit = 0.0

    def on_enter(self) -> None:
        self._layout()
        self._create_stage()

    def _layout(self) -> None:
        w = self.app.screen.get_width()
        h = self.app.screen.get_height()
        self.play_rect.center = (w // 2, h // 2 + 40)

        if self._modal is not None:
            self._modal.resize((w, h))

        if self.stage is not None and hasattr(self.stage, "set_play_rect"):
            self.stage.set_play_rect(self.play_rect)

    def _create_stage(self) -> None:
        settings = load_settings()
        initial_value = int(settings.get("master_volume", 50))

        bal = self.catalog.get_balance(self.stage_id)
        self.stage_time_limit = float(getattr(bal, "time_limit_seconds", 0.0))

        target = None
        slide_mapping = None
        slide_initial_pos = None

        if self.stage_id == "pong_bounce":
            target = random.randint(12, 28)

        elif self.stage_id == "slide_random":
            slide_mapping = make_random_mapping_0_100()
            slide_initial_pos = random.randint(0, 100)

            current_at_start = int(slide_mapping[slide_initial_pos])
            lo = max(0, current_at_start - 30)
            hi = min(100, current_at_start + 30)
            candidates = [v for v in slide_mapping if lo <= v <= hi]
            target = random.choice(candidates) if candidates else random.choice(slide_mapping)

        else:
            target = pick_target_within_range(
                initial_value=initial_value,
                radius=30,
                min_distance=int(getattr(bal, "min_target_distance", 0)),
            )

        if self.stage_id == "slider_normal":
            self.stage = SliderNormalStage(
                target=target,
                play_rect=self.play_rect,
                initial_value=initial_value,
                hold_seconds=float(getattr(bal, "hold_seconds", 0.5)),
                clear_mode=str(getattr(bal, "clear_mode", "hold")),
            )

        elif self.stage_id == "toggle_grid":
            self.stage = ToggleGridStage(
                target=target,
                play_rect=self.play_rect,
                hold_seconds=float(getattr(bal, "hold_seconds", 0.5)),
                clear_mode=str(getattr(bal, "clear_mode", "hold")),
                initial_value=initial_value,
            )

        elif self.stage_id == "cannon_shot":
            self.stage = CannonShotStage(
                target=target,
                play_rect=self.play_rect,
                initial_value=initial_value,
                hold_seconds=float(getattr(bal, "hold_seconds", 0.5)),
                clear_mode=str(getattr(bal, "clear_mode", "hold")),
            )

        elif self.stage_id == "tilt_slider":
            self.stage = TiltSliderStage(
                target=target,
                play_rect=self.play_rect,
                initial_value=initial_value,
                hold_seconds=float(getattr(bal, "hold_seconds", 0.5)),
                clear_mode=str(getattr(bal, "clear_mode", "hold")),
            )

        elif self.stage_id == "scratch_bar":
            self.stage = ScratchBarStage(
                target=target,
                play_rect=self.play_rect,
                initial_value=initial_value,
                hold_seconds=float(getattr(bal, "hold_seconds", 0.5)),
                clear_mode=str(getattr(bal, "clear_mode", "hold")),
            )

        elif self.stage_id == "pong_bounce":
            self.stage = PongBounceStage(
                target=target,
                play_rect=self.play_rect,
                initial_value=initial_value,
                hold_seconds=float(getattr(bal, "hold_seconds", 0.5)),
                clear_mode=str(getattr(bal, "clear_mode", "hold")),
            )

        elif self.stage_id == "slide_random":
            if slide_mapping is None:
                slide_mapping = make_random_mapping_0_100()
            if slide_initial_pos is None:
                slide_initial_pos = random.randint(0, 100)

            self.stage = SlideRandomStage(
                target=int(target),
                play_rect=self.play_rect,
                mapping=slide_mapping,
                initial_position_percent=int(slide_initial_pos),
                hold_seconds=float(getattr(bal, "hold_seconds", 0.5)),
                clear_mode=str(getattr(bal, "clear_mode", "hold")),
            )

        elif self.stage_id == "lever_crank":
            # (추가) 8스테이지 실제 레버 스테이지 생성
            self.stage = LeverCrankStage(
                target=int(target),
                play_rect=self.play_rect,
                initial_value=initial_value,
                hold_seconds=float(getattr(bal, "hold_seconds", 0.5)),
                clear_mode=str(getattr(bal, "clear_mode", "hold")),
            )

        else:
            self.stage = SliderNormalStage(
                target=target,
                play_rect=self.play_rect,
                initial_value=initial_value,
                hold_seconds=float(getattr(bal, "hold_seconds", 0.5)),
                clear_mode=str(getattr(bal, "clear_mode", "hold")),
            )

        self.elapsed = 0.0
        self._cleared_once = False

        self._modal = None
        self._modal_left_action = None
        self._modal_right_action = None

        if self.stage is not None and self.stage.supports_numeric_value():
            cv = self.stage.get_current_value()
            if 0 <= cv <= 100:
                self.app.apply_master_volume(cv / 100.0)

    def _save_progress_unlock_next(self) -> None:
        progress = load_progress()
        highest = int(progress.get("highest_unlocked", 1))
        if self.stage_number >= highest:
            progress["highest_unlocked"] = min(25, highest + 1)
            save_progress(progress)

    def _go_stage_select(self) -> None:
        from .stage_select_scene import StageSelectScene
        self.app.change_scene(StageSelectScene(self.app))

    def _go_home(self) -> None:
        from .main_menu_scene import MainMenuScene
        self.app.change_scene(MainMenuScene(self.app))

    def _go_next_stage(self) -> None:
        next_num = self.stage_number + 1
        next_id = self.catalog.get_stage_id_by_number(next_num)

        if next_id is None:
            self._go_stage_select()
            return

        self.app.change_scene(StagePlayScene(self.app, next_num, next_id, mode=self.mode))

    def _open_modal(
        self,
        title: str,
        message: str,
        left_text: str,
        right_text: str,
        left_action,
        right_action,
    ) -> None:
        w = self.app.screen.get_width()
        h = self.app.screen.get_height()
        self._modal = ModalDialog(
            screen_size=(w, h),
            title=title,
            message=message,
            left_button_text=left_text,
            right_button_text=right_text,
        )
        self._modal_left_action = left_action
        self._modal_right_action = right_action

    def _open_clear_modal_stage_mode(self) -> None:
        self._open_modal(
            title="Cleared",
            message="Stage cleared. Choose next action.",
            left_text="Next Stage",
            right_text="Stage Select",
            left_action=self._go_next_stage,
            right_action=self._go_stage_select,
        )

    def _open_fail_modal_stage_mode_timeover(self) -> None:
        self._open_modal(
            title="Failed",
            message="Time over",
            left_text="Retry",
            right_text="Stage Select",
            left_action=self._create_stage,
            right_action=self._go_stage_select,
        )

    def _open_fail_modal_stage_mode_missed(self) -> None:
        self._open_modal(
            title="Failed",
            message="Missed",
            left_text="Retry",
            right_text="Stage Select",
            left_action=self._create_stage,
            right_action=self._go_stage_select,
        )

    def _on_timeout(self) -> None:
        self.fail_count += 1
        if self.mode == "stage":
            self._open_fail_modal_stage_mode_timeover()
            return
        self._create_stage()

    def _on_missed(self) -> None:
        self.fail_count += 1
        if self.mode == "stage":
            self._open_fail_modal_stage_mode_missed()
            return
        self._create_stage()

    def handle_event(self, event) -> None:
        if event.type == pygame.VIDEORESIZE:
            self._layout()
            return

        if self._modal is not None:
            result = self._modal.handle_event(event)
            if result == "left" and self._modal_left_action is not None:
                self._modal_left_action()
            elif result == "right" and self._modal_right_action is not None:
                self._modal_right_action()
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._go_home()
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            if self.btn_home.rect.collidepoint(mx, my):
                self._go_home()
                return

            if self.btn_stage.rect.collidepoint(mx, my):
                self._go_stage_select()
                return

            if self.btn_restart.rect.collidepoint(mx, my):
                self.fail_count += 1
                self._create_stage()
                return

        if self.stage:
            self.stage.handle_event(event)

            if hasattr(self.stage, "consume_volume_changed"):
                try:
                    changed = bool(self.stage.consume_volume_changed())
                except Exception:
                    changed = False

                if changed and self.stage.supports_numeric_value():
                    cv = self.stage.get_current_value()
                    if 0 <= cv <= 100:
                        self.app.apply_master_volume(cv / 100.0)

    def update(self, dt: float) -> None:
        if self._modal is not None:
            return

        self.elapsed += dt

        if self.stage:
            self.stage.update(dt)

            if hasattr(self.stage, "consume_missed"):
                try:
                    missed = bool(self.stage.consume_missed())
                except Exception:
                    missed = False
                if missed:
                    self._on_missed()
                    return

        if self.stage_time_limit > 0:
            remaining = self.stage_time_limit - self.elapsed
            if remaining <= 0:
                self._on_timeout()
                return

        if self.stage:
            if (not self._cleared_once) and self.stage.is_cleared():
                self._cleared_once = True
                self._save_progress_unlock_next()

                if self.mode == "stage":
                    self._open_clear_modal_stage_mode()
                else:
                    self._go_next_stage()

    def render(self, screen) -> None:
        screen.fill((18, 18, 22))
        mouse = pygame.mouse.get_pos()

        Header.render(
            screen=screen,
            title=f"Stage : {self.stage_number}",
            subtitle=None,
            title_font=self.app.base_font,
            subtitle_font=self.app.small_font,
        )

        self.btn_home.render(screen, self.app.small_font, mouse)
        self.btn_stage.render(screen, self.app.small_font, mouse)
        self.btn_restart.render(screen, self.app.small_font, mouse)

        if self.stage_time_limit > 0:
            t = max(0.0, self.stage_time_limit - self.elapsed)
        else:
            t = self.elapsed

        info = f"Time : {t:.2f}   Fails : {self.fail_count}"
        surf = self.app.small_font.render(info, True, (230, 230, 230))
        screen.blit(surf, (screen.get_width() - surf.get_width() - 20, 25))

        pygame.draw.rect(screen, (0, 0, 0), self.play_rect)
        pygame.draw.rect(screen, (90, 90, 100), self.play_rect, 2)

        if self.stage:
            target_text = f"Target : {self.stage.get_target_value()}"
            t1 = self.app.small_font.render(target_text, True, (230, 230, 230))
            screen.blit(t1, (self.play_rect.left + 20, self.play_rect.top + 20))

            if self.stage.supports_numeric_value():
                current_value = int(self.stage.get_current_value())
            else:
                current_value = None

            meter_w = 44
            meter_h = 190
            pad_right = 20
            pad_top = 12
            meter_rect = pygame.Rect(
                self.play_rect.right - pad_right - meter_w,
                self.play_rect.top + pad_top,
                meter_w,
                meter_h,
            )
            _draw_vertical_volume_meter(screen, meter_rect, current_value, self.app.small_font)

            prev_clip = screen.get_clip()
            screen.set_clip(self.play_rect)
            self.stage.render(screen)
            screen.set_clip(prev_clip)

        if self._modal is not None:
            self._modal.render(
                screen,
                title_font=self.app.base_font,
                body_font=self.app.small_font,
            )
