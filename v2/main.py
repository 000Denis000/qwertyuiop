#!/usr/bin/env python3
# ============================================================
#  BACKYARD SURVIVAL v2  –  Entry Point
#  Run:  python main.py
#  Deps: pip install ursina
# ============================================================
import sys
import os

# Ensure v2/ directory is on the path
sys.path.insert(0, os.path.dirname(__file__))

from ursina import Ursina, window, color, Text, camera, Entity
from constants import WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT, TARGET_FPS


def show_loading_screen(app):
    from ursina import camera
    loading_text = Text(
        "BACKYARD SURVIVAL\n\nGenerating world...",
        parent=camera.ui,
        position=(0, 0),
        scale=1.0,
        color=color.rgba(80, 220, 80, 255),
        origin=(0, 0),
    )
    app.step()   # render one frame so loading screen shows
    return loading_text


def main():
    app = Ursina(
        title     = WINDOW_TITLE,
        borderless= False,
        fullscreen= False,
        size      = (WINDOW_WIDTH, WINDOW_HEIGHT),
        vsync     = True,
    )
    window.fps_counter.enabled  = True
    window.exit_button.visible  = False
    window.color                = color.rgb(10, 15, 10)

    # Show loading splash
    from ursina import camera as ucam
    splash = show_loading_screen(app)

    # Build the game (world gen happens here)
    from game import Game
    game = Game()

    # Remove loading screen
    from ursina import destroy
    destroy(splash)

    # Hook Ursina callbacks into game
    from ursina import Entity, time as utime

    class GameHook(Entity):
        def __init__(self, g):
            super().__init__()
            self.g = g
        def update(self):
            self.g.update()
        def input(self, key):
            self.g.input(key)

    GameHook(game)

    app.run()


if __name__ == "__main__":
    main()
