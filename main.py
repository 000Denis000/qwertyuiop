# main.py - Entry point for Backyard Survival

import pygame
import sys
from game import Game
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, GAME_TITLE


def main():
    pygame.init()
    pygame.display.set_caption(GAME_TITLE)
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock  = pygame.time.Clock()

    # Show loading screen
    font = pygame.font.SysFont("monospace", 32, bold=True)
    screen.fill((10, 15, 10))
    loading = font.render("Generating world...", True, (100, 220, 80))
    screen.blit(loading, (SCREEN_WIDTH//2 - loading.get_width()//2,
                           SCREEN_HEIGHT//2 - loading.get_height()//2))
    pygame.display.flip()

    game = Game(screen, clock)
    game.run()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
