from __future__ import annotations

import pygame

from ..core.scene_base import Scene
from ..systems.persist import load_settings, save_settings
from ..ui.widgets import Button, Toast
from ..ui.header import Header
from ..ui.modal_dialog import ModalDialog

from .stage_select_scene import StageSelectScene
from .challenge_scene import ChallengeScene
from .developer_scene import DeveloperScene
from .options_scene import OptionsScene


class MainMenuScene(Scene):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.toast = Toast()

        self.btn_stage = Button(pygame.Rect(0, 0, 360, 64), "Stage Mode")
        self.btn_challenge = Button(pygame.Rect(0, 0, 360, 64), "Challenge Mode")
        self.btn_option = Button(pygame.Rect(0, 0, 360, 64), "Option")
        self.btn_dev = Button(pygame.Rect(0, 0, 360, 64), "Developer")

        # (요구사항 3) 최초 1회 경고 모달
        self._modal: ModalDialog | None = None
        self._modal_left_action = None
        self._modal_right_action = None

    def on_enter(self) -> None:
        self._layout()
        self._maybe_show_warning_once()

    def _layout(self) -> None:
        cx = self.app.screen.get_width() // 2
        top = 210
        gap = 18
        buttons = [self.btn_stage, self.btn_challenge, self.btn_option, self.btn_dev]
        for i, b in enumerate(buttons):
            b.rect.center = (cx, top + i * (b.rect.height + gap))

        if self._modal is not None:
            w = self.app.screen.get_width()
            h = self.app.screen.get_height()
            self._modal.resize((w, h))

    def _open_modal(self, title: str, message: str) -> None:
        w = self.app.screen.get_width()
        h = self.app.screen.get_height()
        self._modal = ModalDialog(
            screen_size=(w, h),
            title=title,
            message=message,
            left_button_text="OK",
            right_button_text="OK",
        )

    def _maybe_show_warning_once(self) -> None:
        s = load_settings()
        if bool(s.get("warning_shown", False)):
            return

        # 임시 문구 (나중에 네가 문구 주면 여기만 교체)
        title = "Warning"
        message = "Temporary warning message.\n(Replace later)"

        self._open_modal(title, message)

        def _close_and_mark() -> None:
            s2 = load_settings()
            s2["warning_shown"] = True
            save_settings(s2)
            self._modal = None

        self._modal_left_action = _close_and_mark
        self._modal_right_action = _close_and_mark

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.VIDEORESIZE:
            self._layout()

        # 모달이 떠 있으면, 모달부터 처리
        if self._modal is not None:
            result = self._modal.handle_event(event)
            if result == "left" and self._modal_left_action is not None:
                self._modal_left_action()
            elif result == "right" and self._modal_right_action is not None:
                self._modal_right_action()
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.app.quit()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse = event.pos
            if self.btn_stage.enabled and self.btn_stage.rect.collidepoint(mouse):
                self.app.change_scene(StageSelectScene(self.app))
                return
            if self.btn_challenge.enabled and self.btn_challenge.rect.collidepoint(mouse):
                self.app.change_scene(ChallengeScene(self.app))
                return
            if self.btn_option.enabled and self.btn_option.rect.collidepoint(mouse):
                self.app.change_scene(OptionsScene(self.app))
                return
            if self.btn_dev.enabled and self.btn_dev.rect.collidepoint(mouse):
                self.app.change_scene(DeveloperScene(self.app))
                return

    def update(self, dt: float) -> None:
        self.toast.update(dt)

    def render(self, screen: pygame.Surface) -> None:
        screen.fill((18, 18, 22))
        mouse = pygame.mouse.get_pos()

        Header.render(
            screen=screen,
            title="Volume Gimmick",
            subtitle="Stage Mode / Challenge Mode / Option / Developer",
            title_font=self.app.base_font,
            subtitle_font=self.app.small_font,
        )

        for b in [self.btn_stage, self.btn_challenge, self.btn_option, self.btn_dev]:
            b.render(screen, self.app.base_font, mouse)

        self.toast.render(screen, self.app.small_font)

        if self._modal is not None:
            self._modal.render(screen, title_font=self.app.base_font, body_font=self.app.small_font)
