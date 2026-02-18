import pygame

from .app import App
from .config import WIDTH, HEIGHT, WINDOW_FLAGS, VSYNC
from .scenes.main_menu_scene import MainMenuScene


def run() -> None:
    pygame.init()

    app = App(
        width=WIDTH,
        height=HEIGHT,
        caption="Volume Gimmick - Prototype",
        flags=WINDOW_FLAGS,
        vsync=VSYNC,
    )
    app.change_scene(MainMenuScene(app))
    app.run()

    pygame.quit()
