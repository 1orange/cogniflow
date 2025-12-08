"""View for MenuScene - handles all rendering."""

import pygame as pg


class MenuView:
    """View for MenuScene - handles rendering only, no state modification."""

    def __init__(self, screen):
        self.screen = screen
        self.colors = {
            "white": (255, 255, 255),
            "green": (0, 200, 0),
            "yellow": (220, 200, 0),
            "red": (200, 60, 60),
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

    def render(self, model):
        """Render the menu screen."""
        W, H = self.screen.get_size()
        self.screen.fill(self.colors["dark_bg"])

        # Title
        self.draw_text("Cogniflow", W // 2, 90, 48, self.colors["white"], True)

        # Menu options
        self.draw_text("[C] Calibrate", W // 2, 200, 36, self.colors["green"], True)
        self.draw_text("[R] Record Data", W // 2, 240, 36, self.colors["green"], True)
        self.draw_text(
            "[M] ML Pipeline (Modulus)", W // 2, 280, 36, self.colors["green"], True
        )
        self.draw_text("[D] Drive (BCI)", W // 2, 320, 36, self.colors["green"], True)
        self.draw_text(
            "[A] Drive (Arrow Keys)", W // 2, 360, 36, self.colors["green"], True
        )
        self.draw_text("[ESC] Quit", W // 2, 420, 28, self.colors["yellow"], True)

        # Model status
        model_status = model.get_model_status()
        model_color = (
            self.colors["green"] if model_status["exists"] else self.colors["red"]
        )
        self.draw_text(
            f"Model: {model_status['status']}",
            W // 2,
            510,
            22,
            model_color,
            True,
        )
