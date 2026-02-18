from __future__ import annotations

import pygame


class Scene:
    """
    모든 Scene이 상속하는 베이스 클래스.

    규칙:
    - 모든 씬은 __init__(app)에서 super().__init__(app)을 호출해야 한다.
    - App은 현재 Scene에 다음 메서드들을 호출한다:
      on_enter(), on_exit(), handle_event(event), update(dt), render(screen)
    """

    def __init__(self, app) -> None:
        self.app = app

    def on_enter(self) -> None:
        pass

    def on_exit(self) -> None:
        pass

    def handle_event(self, event: pygame.event.Event) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def render(self, screen: pygame.Surface) -> None:
        pass
