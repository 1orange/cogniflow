import pygame as pg


class BaseScene:
    """Base class for all trainer scenes with common functionality."""

    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock
        self.running = False

        # Common colors
        self.colors = {
            "white": (255, 255, 255),
            "grey": (40, 40, 40),
            "green": (0, 200, 0),
            "red": (200, 60, 60),
            "yellow": (220, 200, 0),
            "blue": (0, 120, 220),
            "dark_bg": (15, 15, 18),
        }

    def draw_text(self, text, x, y, size=28, color=None, center=False):
        """Draw text on the screen."""
        if color is None:
            color = self.colors["white"]
        font = pg.font.SysFont("Arial", size)
        img = font.render(text, True, color)
        rect = img.get_rect()
        if center:
            rect.center = (x, y)
        else:
            rect.topleft = (x, y)
        self.screen.blit(img, rect)

    def arrow_surface(self, direction, size=100, color=None):
        """Create an arrow surface for the given direction."""
        if color is None:
            color = self.colors["white"]
        surf = pg.Surface((size, size), pg.SRCALPHA)
        c = size // 2

        if direction == "left":
            pg.draw.polygon(
                surf,
                color,
                [
                    (size * 0.75, c),
                    (size * 0.25, c),
                    (size * 0.4, c * 0.6),
                    (size * 0.25, c),
                    (size * 0.4, c * 1.4),
                ],
            )
        elif direction == "right":
            pg.draw.polygon(
                surf,
                color,
                [
                    (size * 0.25, c),
                    (size * 0.75, c),
                    (size * 0.6, c * 0.6),
                    (size * 0.75, c),
                    (size * 0.6, c * 1.4),
                ],
            )
        elif direction == "forward":
            pg.draw.polygon(
                surf,
                color,
                [
                    (c, size * 0.75),
                    (c, size * 0.25),
                    (c * 0.6, size * 0.4),
                    (c, size * 0.25),
                    (c * 1.4, size * 0.4),
                ],
            )
        elif direction == "backward":
            pg.draw.polygon(
                surf,
                color,
                [
                    (c, size * 0.25),
                    (c, size * 0.75),
                    (c * 0.6, size * 0.6),
                    (c, size * 0.75),
                    (c * 1.4, size * 0.6),
                ],
            )
        return surf

    def run(self):
        """Override this method in subclasses to implement scene logic."""
        raise NotImplementedError("Subclasses must implement the run method")
