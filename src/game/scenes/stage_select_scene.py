from __future__ import annotations

import json
from pathlib import Path

import pygame

from ..core.scene_base import Scene
from ..systems.persist import load_progress
from ..systems.stage_catalog import StageCatalog
from ..ui.header import Header
from ..ui.widgets import Button, Toast
from .stage_play_scene import StagePlayScene

CATALOG_PATH = Path("src/game/data/stage_catalog.json")


def _load_catalog_raw():
    with open(CATALOG_PATH, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    return data.get("stages", [])


class StageSelectScene(Scene):
    def __init__(self, app) -> None:
        super().__init__(app)

        self.toast = Toast()
        self.catalog = StageCatalog.load()
        self.stages = _load_catalog_raw()

        self.buttons: list[tuple[int, str, bool, pygame.Rect]] = []
        self.unlocked = 1

        self.btn_home = Button(pygame.Rect(20, 20, 120, 40), "Home")

        # 해골 아이콘(이번 패치: 항상 보이도록)
        self.skull_rect = pygame.Rect(0, 0, 18, 18)
        
        # 아이콘은 이모지 렌더 대신, 임시로 흰 정사각형 이미지(Surface)로 표시한다.
        # 나중에 원하는 PNG로 바꿀 때는 pygame.image.load(...)로 교체하면 된다.
        self.skull_image = pygame.Surface((18, 18), pygame.SRCALPHA)
        self.skull_image.fill((255, 255, 255, 255))


    def on_enter(self) -> None:
        self._build_grid()

    def _build_grid(self) -> None:
        self.buttons.clear()

        progress = load_progress()
        self.unlocked = int(progress.get("highest_unlocked", 1))

        screen_w = self.app.screen.get_width()
        screen_h = self.app.screen.get_height()

        cols = 5
        rows = 5

        top_reserved = 160
        bottom_reserved = 70

        # 그리드를 더 크게 보이게 하되 바깥 여백은 남기기
        left_pad = 42
        right_pad = 42

        avail_w = max(1, screen_w - left_pad - right_pad)
        avail_h = max(1, screen_h - top_reserved - bottom_reserved)

        # 타일 크게(화면을 채우는 느낌)
        tile = int(min(avail_w / cols, avail_h / rows))
        tile = max(76, tile)

        # spacing을 조금 줄여 타일이 더 커 보이도록
        spacing = int(tile * 0.16)
        spacing = max(12, spacing)

        grid_w = cols * tile + (cols - 1) * spacing
        grid_h = rows * tile + (rows - 1) * spacing

        # 세로 초과 시 축소
        if grid_h > avail_h:
            tile = int((avail_h - (rows - 1) * 12) / rows)
            tile = max(64, tile)
            spacing = max(10, int(tile * 0.16))
            grid_w = cols * tile + (cols - 1) * spacing
            grid_h = rows * tile + (rows - 1) * spacing

        # 가로 초과 시 축소
        if grid_w > avail_w:
            tile = int((avail_w - (cols - 1) * 12) / cols)
            tile = max(64, tile)
            spacing = max(10, int(tile * 0.16))
            grid_w = cols * tile + (cols - 1) * spacing
            grid_h = rows * tile + (rows - 1) * spacing

        start_x = (screen_w - grid_w) // 2
        start_y = top_reserved + (avail_h - grid_h) // 2

        for idx in range(25):
            row = idx // cols
            col = idx % cols

            rect = pygame.Rect(
                start_x + col * (tile + spacing),
                start_y + row * (tile + spacing),
                tile,
                tile,
            )

            stage_number = idx + 1
            meta = self.stages[idx] if idx < len(self.stages) else {"id": f"tbd_{stage_number:02d}", "implemented": False}
            stage_id = str(meta.get("id", f"tbd_{stage_number:02d}"))
            implemented = bool(meta.get("implemented", False))

            self.buttons.append((stage_number, stage_id, implemented, rect))

        # 해골 아이콘 위치(홈 버튼 오른쪽, 아주 작게)
        self.skull_rect.size = (18, 18)
        self.skull_rect.left = self.btn_home.rect.right + 8
        self.skull_rect.centery = self.btn_home.rect.centery

    def handle_event(self, event) -> None:
        if event.type == pygame.VIDEORESIZE:
            self._build_grid()
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            from .main_menu_scene import MainMenuScene
            self.app.change_scene(MainMenuScene(self.app))
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            if self.btn_home.rect.collidepoint(mx, my):
                from .main_menu_scene import MainMenuScene
                self.app.change_scene(MainMenuScene(self.app))
                return

            # 해골 아이콘 클릭(이번 패치: 미구현 토스트만)
            # 원래 설계: 25스테이지까지 모두 클리어했을 때만 표시/활성화
            if self.skull_rect.collidepoint(mx, my):
                self.toast.show("미구현 스테이지.")
                return

            for stage_number, stage_id, implemented, rect in self.buttons:
                if rect.collidepoint(mx, my):
                    if stage_number > self.unlocked:
                        return
                    if not implemented or stage_id.startswith("tbd_"):
                        self.toast.show("미구현 스테이지.")
                        return
                    self.app.change_scene(StagePlayScene(self.app, stage_number, stage_id, mode="stage"))
                    return

    def update(self, dt: float) -> None:
        self.toast.update(dt)

    def render(self, screen) -> None:
        screen.fill((18, 18, 22))
        mouse = pygame.mouse.get_pos()

        Header.render(
            screen=screen,
            title="Stage Mode",
            subtitle=None,
            title_font=self.app.base_font,
            subtitle_font=self.app.small_font,
        )

        self.btn_home.render(screen, self.app.small_font, mouse)

        screen.blit(self.skull_image, self.skull_rect.topleft)


        font = self.app.small_font

        for stage_number, stage_id, implemented, rect in self.buttons:
            locked = stage_number > self.unlocked

            if locked:
                color = (50, 50, 60)
            else:
                if not implemented or stage_id.startswith("tbd_"):
                    color = (70, 70, 85)
                else:
                    color = (80, 110, 200)

            pygame.draw.rect(screen, color, rect, border_radius=10)
            pygame.draw.rect(screen, (120, 120, 130), rect, 2, border_radius=10)

            text = font.render(str(stage_number), True, (240, 240, 240))
            screen.blit(
                text,
                (
                    rect.centerx - text.get_width() // 2,
                    rect.centery - text.get_height() // 2,
                ),
            )

        self.toast.render(screen, self.app.small_font)
