from __future__ import annotations

import sys
import pygame

from .config import FPS
from .core.scene_base import Scene


class App:
    def __init__(self, width: int, height: int, caption: str, flags: int = 0, vsync: int = 0) -> None:
        self.width = width
        self.height = height

        # mixer는 사운드가 생길 때를 대비해 초기화
        # 실패해도 게임이 죽지 않게 try 처리
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except Exception:
            pass

        self.screen = pygame.display.set_mode((width, height), flags=flags, vsync=vsync)
        pygame.display.set_caption(caption)

        self.clock = pygame.time.Clock()
        self.running = True

        self.scene: Scene | None = None

        # 한글 글리프 폰트(임시)
        self.base_font = pygame.font.SysFont("malgungothic", 30) or pygame.font.SysFont(None, 30)
        self.small_font = pygame.font.SysFont("malgungothic", 20) or pygame.font.SysFont(None, 20)

        # 게임 내부 마스터 볼륨(0.0~1.0)
        self.master_volume = 0.5
        self.apply_master_volume(self.master_volume)

    def apply_master_volume(self, volume_01: float) -> None:
        """
        게임 내부 볼륨(0.0~1.0)을 pygame mixer에 적용.
        - OS 볼륨과 독립적이며, 게임이 재생하는 사운드만 영향을 받음.
        """
        v = max(0.0, min(1.0, float(volume_01)))
        self.master_volume = v

        try:
            # music은 전역 볼륨이 있음
            pygame.mixer.music.set_volume(v)
        except Exception:
            pass

        # Sound 객체 개별 볼륨은 생성 시점에 설정하는 게 정석이라,
        # 추후 AudioManager를 두고 재생 시 곱해주는 방식으로 확장할 예정.
        # (현재는 사운드 리소스가 없으므로 여기까지로 충분)

    def change_scene(self, next_scene: Scene) -> None:
        if self.scene is not None:
            self.scene.on_exit()
        self.scene = next_scene
        self.scene.on_enter()

    def quit(self) -> None:
        self.running = False

    def run(self) -> None:
        while self.running:
            dt_ms = self.clock.tick(FPS)
            dt = dt_ms / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break
                if self.scene is not None:
                    self.scene.handle_event(event)

            if not self.running:
                break

            if self.scene is not None:
                self.scene.update(dt)
                self.scene.render(self.screen)

            pygame.display.flip()

        pygame.quit()
        sys.exit(0)
