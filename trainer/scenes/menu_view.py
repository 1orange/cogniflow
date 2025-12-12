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
            "cyan": (0, 180, 180),
            "dark_bg": (15, 15, 18),
            "light_grey": (100, 100, 100),
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
        self.draw_text("Cogniflow", W // 2, 70, 48, self.colors["white"], True)
        self.draw_text(
            "BCI Car Trainer", W // 2, 110, 20, self.colors["light_grey"], True
        )

        # Menu options
        menu_start_y = 170
        line_height = 38
        
        self.draw_text("[C] Calibrate", W // 2, menu_start_y, 32, self.colors["green"], True)
        self.draw_text("[R] Record Data", W // 2, menu_start_y + line_height, 32, self.colors["green"], True)
        self.draw_text(
            "[M] ML Pipeline (Modulus)", W // 2, menu_start_y + line_height * 2, 32, self.colors["green"], True
        )
        self.draw_text(
            "[L] Live BCI → MQTT", W // 2, menu_start_y + line_height * 3, 32, self.colors["cyan"], True
        )
        self.draw_text("[D] Drive (BCI)", W // 2, menu_start_y + line_height * 4, 32, self.colors["green"], True)
        self.draw_text(
            "[A] Drive (Arrow Keys)", W // 2, menu_start_y + line_height * 5, 32, self.colors["green"], True
        )
        self.draw_text("[ESC] Quit", W // 2, menu_start_y + line_height * 6 + 20, 26, self.colors["yellow"], True)

        # Model status
        model_status = model.get_model_status()
        model_color = (
            self.colors["green"] if model_status["exists"] else self.colors["red"]
        )
        self.draw_text(
            f"Model: {model_status['status']}",
            W // 2,
            H - 80,
            20,
            model_color,
            True,
        )
        
        # Source info
        source_info = model.source_info
        if source_info["sample_rate"]:
            self.draw_text(
                f"EEG: {source_info['name']} @ {source_info['sample_rate']}Hz, {source_info['channels']}ch",
                W // 2,
                H - 50,
                16,
                self.colors["light_grey"],
                True,
            )
