"""
BCI Car Trainer Game Module

A modular trainer system for brain-computer interface car control training.
"""

import pygame as pg


def main():
    """Main entry point for the BCI Car Trainer application."""
    from .scenes.menu import MenuScene

    pg.init()
    W, H = 1280, 720  # Larger default window size for better pseudo-3D experience
    screen = pg.display.set_mode((W, H))
    pg.display.set_caption("BCI Car Trainer")
    clock = pg.time.Clock()

    # Create and run the menu
    menu = MenuScene(screen, clock)
    menu.run()

    pg.quit()


__all__ = ["main"]
