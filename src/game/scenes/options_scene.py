from __future__ import annotations

import pygame

from ..core.scene_base import Scene
from ..systems.persist import load_settings, save_settings
from ..ui.widgets import Button, Toast
from ..ui.header import Header
from ..ui.slider import Slider


def _clamp_int(x: int, lo: int, hi: int) -> int:
    return lo if x < lo else hi if x > hi else x


class OptionsScene(Scene):
    MASTER_VOLUME_MAX = 70  # 기존 요구사항 유지: 0~70까지만 허용
    OUTPUT_GAIN_MAX = 100   # 신규 요구사항: 0~100%

    def __init__(self, app) -> None:
        super().__init__(app)
        self.toast = Toast()

        self.btn_home = Button(pygame.Rect(22, 18, 120, 42), "Home")

        s = load_settings()

        v = int(s.get("master_volume", 50))
        v = _clamp_int(v, 0, self.MASTER_VOLUME_MAX)

        g = int(s.get("output_gain", 100))
        g = _clamp_int(g, 0, self.OUTPUT_GAIN_MAX)

        self.slider_volume = Slider(pygame.Rect(0, 0, 420, 54), value=v)
        self.slider_gain = Slider(pygame.Rect(0, 0, 420, 54), value=g)

    def on_enter(self) -> None:
        self._layout()

    def _layout(self) -> None:
        cx = self.app.screen.get_width() // 2
        self.slider_volume.rect.center = (cx, 300)
        self.slider_gain.rect.center = (cx, 420)

    def _save_master_volume(self, v: int) -> None:
        v = _clamp_int(int(v), 0, self.MASTER_VOLUME_MAX)

        # 기존 설정 키들을 날리지 않도록 merge 저장
        s = load_settings()
        s["master_volume"] = v
        save_settings(s)

        # 기본 볼륨 반영 (0.70 스케일 유지: 70 -> 0.70)
        self.app.apply_master_volume(v / 100.0)

    def _save_output_gain(self, g: int) -> None:
        g = _clamp_int(int(g), 0, self.OUTPUT_GAIN_MAX)

        # 기존 설정 키들을 날리지 않도록 merge 저장
        s = load_settings()
        s["output_gain"] = g
        save_settings(s)

        # 최종 출력 배율 반영
        self.app.apply_output_gain(g / 100.0)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.VIDEORESIZE:
            self._layout()

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            from .main_menu_scene import MainMenuScene
            self.app.change_scene(MainMenuScene(self.app))
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_home.rect.collidepoint(event.pos):
                from .main_menu_scene import MainMenuScene
                self.app.change_scene(MainMenuScene(self.app))
                return

        # 슬라이더(기본 볼륨) 값 변화 처리
        if self.slider_volume.handle_event(event):
            self.slider_volume.value = _clamp_int(int(self.slider_volume.value), 0, self.MASTER_VOLUME_MAX)
            self._save_master_volume(self.slider_volume.value)

        # 슬라이더(최종 출력 배율) 값 변화 처리
        if self.slider_gain.handle_event(event):
            self.slider_gain.value = _clamp_int(int(self.slider_gain.value), 0, self.OUTPUT_GAIN_MAX)
            self._save_output_gain(self.slider_gain.value)

    def update(self, dt: float) -> None:
        self.toast.update(dt)

    def render(self, screen: pygame.Surface) -> None:
        screen.fill((18, 18, 22))
        mouse = pygame.mouse.get_pos()

        self.btn_home.render(screen, self.app.small_font, mouse)

        Header.render(
            screen=screen,
            title="Option",
            subtitle="Master volume and final output gain",
            title_font=self.app.base_font,
            subtitle_font=self.app.small_font,
        )

        # 라벨 1: 기본 볼륨
        label1 = self.app.small_font.render(f"Master Volume: {self.slider_volume.value}", True, (230, 230, 230))
        screen.blit(label1, (self.slider_volume.rect.left, self.slider_volume.rect.top - 28))
        self.slider_volume.render(screen)

        # 라벨 2: 최종 출력 배율
        label2 = self.app.small_font.render(f"Output Gain: {self.slider_gain.value}%", True, (230, 230, 230))
        screen.blit(label2, (self.slider_gain.rect.left, self.slider_gain.rect.top - 28))
        self.slider_gain.render(screen)

        # 아래쪽 예약 영역 박스(기존 유지)
        box = pygame.Rect(60, 520, screen.get_width() - 120, screen.get_height() - 580)
        if box.height > 0:
            pygame.draw.rect(screen, (30, 30, 36), box, border_radius=14)
            pygame.draw.rect(screen, (80, 80, 95), box, width=2, border_radius=14)

            hint = self.app.small_font.render("Reserved area for future settings.", True, (190, 190, 190))
            screen.blit(hint, (80, box.top + 20))

        self.toast.render(screen, self.app.small_font)
