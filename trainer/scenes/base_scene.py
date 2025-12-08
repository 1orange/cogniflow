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
            # Arrow pointing left
            pg.draw.polygon(
                surf,
                color,
                [
                    (size * 0.2, c),  # tip (left)
                    (size * 0.5, size * 0.25),  # upper wing
                    (size * 0.5, size * 0.4),  # upper shaft
                    (size * 0.8, size * 0.4),  # upper right
                    (size * 0.8, size * 0.6),  # lower right
                    (size * 0.5, size * 0.6),  # lower shaft
                    (size * 0.5, size * 0.75),  # lower wing
                ],
            )
        elif direction == "right":
            # Arrow pointing right
            pg.draw.polygon(
                surf,
                color,
                [
                    (size * 0.8, c),  # tip (right)
                    (size * 0.5, size * 0.25),  # upper wing
                    (size * 0.5, size * 0.4),  # upper shaft
                    (size * 0.2, size * 0.4),  # upper left
                    (size * 0.2, size * 0.6),  # lower left
                    (size * 0.5, size * 0.6),  # lower shaft
                    (size * 0.5, size * 0.75),  # lower wing
                ],
            )
        elif direction == "forward":
            # Arrow pointing up
            pg.draw.polygon(
                surf,
                color,
                [
                    (c, size * 0.2),  # tip (up)
                    (size * 0.25, size * 0.5),  # left wing
                    (size * 0.4, size * 0.5),  # left shaft
                    (size * 0.4, size * 0.8),  # bottom left
                    (size * 0.6, size * 0.8),  # bottom right
                    (size * 0.6, size * 0.5),  # right shaft
                    (size * 0.75, size * 0.5),  # right wing
                ],
            )
        elif direction == "backward":
            # Arrow pointing down
            pg.draw.polygon(
                surf,
                color,
                [
                    (c, size * 0.8),  # tip (down)
                    (size * 0.25, size * 0.5),  # left wing
                    (size * 0.4, size * 0.5),  # left shaft
                    (size * 0.4, size * 0.2),  # top left
                    (size * 0.6, size * 0.2),  # top right
                    (size * 0.6, size * 0.5),  # right shaft
                    (size * 0.75, size * 0.5),  # right wing
                ],
            )
        return surf

    def run(self):
        """Override this method in subclasses to implement scene logic."""
        raise NotImplementedError("Subclasses must implement the run method")
