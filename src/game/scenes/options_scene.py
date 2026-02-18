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
    MASTER_VOLUME_MAX = 70  # (요구사항 2) 0~70까지만 허용

    def __init__(self, app) -> None:
        super().__init__(app)
        self.toast = Toast()

        self.btn_home = Button(pygame.Rect(22, 18, 120, 42), "Home")

        s = load_settings()
        v = int(s.get("master_volume", 50))
        v = _clamp_int(v, 0, self.MASTER_VOLUME_MAX)

        self.slider_volume = Slider(pygame.Rect(0, 0, 420, 54), value=v)

    def on_enter(self) -> None:
        self._layout()

    def _layout(self) -> None:
        cx = self.app.screen.get_width() // 2
        self.slider_volume.rect.center = (cx, 300)

    def _save_master_volume(self, v: int) -> None:
        v = _clamp_int(int(v), 0, self.MASTER_VOLUME_MAX)

        # (중요) 기존 설정 키들을 날리지 않도록 merge 저장
        s = load_settings()
        s["master_volume"] = v
        save_settings(s)

        # 70이면 0.70으로 반영(기존 0~100 스케일 유지)
        self.app.apply_master_volume(v / 100.0)

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

        # 슬라이더 값 변화 처리
        if self.slider_volume.handle_event(event):
            # Slider가 0~100을 전제로 움직일 수도 있으므로 여기서 강제 clamp
            self.slider_volume.value = _clamp_int(int(self.slider_volume.value), 0, self.MASTER_VOLUME_MAX)
            self._save_master_volume(self.slider_volume.value)

    def update(self, dt: float) -> None:
        self.toast.update(dt)

    def render(self, screen: pygame.Surface) -> None:
        screen.fill((18, 18, 22))
        mouse = pygame.mouse.get_pos()

        self.btn_home.render(screen, self.app.small_font, mouse)

        Header.render(
            screen=screen,
            title="Option",
            subtitle="Game master volume (independent from OS volume)",
            title_font=self.app.base_font,
            subtitle_font=self.app.small_font,
        )

        # 라벨
        label = self.app.small_font.render(f"Volume: {self.slider_volume.value}", True, (230, 230, 230))
        screen.blit(label, (self.slider_volume.rect.left, self.slider_volume.rect.top - 28))

        # 슬라이더
        self.slider_volume.render(screen)

        # 아래쪽에 향후 설정이 추가될 공간이 있다는 것을 보여주는 박스(레이아웃 자리잡기)
        box = pygame.Rect(60, 360, screen.get_width() - 120, screen.get_height() - 420)
        pygame.draw.rect(screen, (30, 30, 36), box, border_radius=14)
        pygame.draw.rect(screen, (80, 80, 95), box, width=2, border_radius=14)

        hint = self.app.small_font.render("Reserved area for future settings.", True, (190, 190, 190))
        screen.blit(hint, (80, 380))

        self.toast.render(screen, self.app.small_font)
