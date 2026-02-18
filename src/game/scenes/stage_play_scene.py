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

from ..systems.persist import load_progress, save_progress, load_settings
from ..systems.stage_catalog import StageCatalog
from ..ui.widgets import Button, Toast
from ..ui.header import Header
from ..ui.modal_dialog import ModalDialog


def pick_target_avoiding_near(initial_value: int, min_distance: int) -> int:
    lo = max(0, initial_value - min_distance)
    hi = min(100, initial_value + min_distance)
    candidates = [x for x in range(0, 101) if not (lo <= x <= hi)]
    return random.choice(candidates) if candidates else random.randint(0, 100)


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

        # 중앙 플레이 프레임
        self.play_rect = pygame.Rect(0, 0, 860, 440)

        self.stage = None
        self._cleared_once = False

        # 모달(성공/실패 공용)
        self._modal: ModalDialog | None = None
        self._modal_left_action = None
        self._modal_right_action = None

        # 스테이지별 제한시간(0이면 제한 없음)
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

        # pong_bounce는 "튕김 횟수 목표"로 별도 생성
        if self.stage_id == "pong_bounce":
            target = random.randint(12, 28)
        else:
            target = pick_target_avoiding_near(initial_value, int(getattr(bal, "min_target_distance", 0)))

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
        else:
            # 알 수 없는 스테이지는 안전하게 기본 슬라이더로 폴백
            self.stage = SliderNormalStage(
                target=target,
                play_rect=self.play_rect,
                initial_value=initial_value,
                hold_seconds=float(getattr(bal, "hold_seconds", 0.5)),
                clear_mode=str(getattr(bal, "clear_mode", "hold")),
            )

        self.elapsed = 0.0
        self._cleared_once = False

        # 모달 닫기
        self._modal = None
        self._modal_left_action = None
        self._modal_right_action = None

        # BGM(또는 마스터 볼륨) 반영: 숫자 값 지원 스테이지만
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

        # challenge에서는 즉시 재시작(모달 없음)
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

            # 값 변경(= 볼륨/점수 등) 반영
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

        # 스테이지 update
        if self.stage:
            self.stage.update(dt)

            # (pong) 미스 실패 처리
            if hasattr(self.stage, "consume_missed"):
                try:
                    missed = bool(self.stage.consume_missed())
                except Exception:
                    missed = False
                if missed:
                    self._on_missed()
                    return

        # 제한시간 처리(0이면 제한 없음)
        if self.stage_time_limit > 0:
            remaining = self.stage_time_limit - self.elapsed
            if remaining <= 0:
                self._on_timeout()
                return

        # 클리어 처리
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

        # 우상단 정보: 제한시간이면 남은 시간, 아니면 경과 시간
        if self.stage_time_limit > 0:
            t = max(0.0, self.stage_time_limit - self.elapsed)
        else:
            t = self.elapsed

        info = f"Time : {t:.2f}   Fails : {self.fail_count}"
        surf = self.app.small_font.render(info, True, (230, 230, 230))
        screen.blit(surf, (screen.get_width() - surf.get_width() - 20, 25))

        # 플레이 프레임
        pygame.draw.rect(screen, (0, 0, 0), self.play_rect)
        pygame.draw.rect(screen, (90, 90, 100), self.play_rect, 2)

        if self.stage:
            target_text = f"Target : {self.stage.get_target_value()}"

            if self.stage.supports_numeric_value():
                current_text = f"Current : {self.stage.get_current_value()}"
            else:
                current_text = "Current : N/A"

            t1 = self.app.small_font.render(target_text, True, (230, 230, 230))
            t2 = self.app.small_font.render(current_text, True, (200, 200, 200))

            screen.blit(t1, (self.play_rect.left + 20, self.play_rect.top + 20))
            screen.blit(t2, (self.play_rect.right - t2.get_width() - 20, self.play_rect.top + 20))

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
