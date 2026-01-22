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
        menu_start_y = 160
        line_height = 36
        
        self.draw_text("[L] Live Drive", W // 2, menu_start_y, 30, self.colors["cyan"], True)
        self.draw_text("[A] Drive (Arrow Keys)", W // 2, menu_start_y + line_height, 30, self.colors["green"], True)
        self.draw_text("[R] Record", W // 2, menu_start_y + line_height * 2, 30, self.colors["green"], True)
        self.draw_text("[M] Modulus", W // 2, menu_start_y + line_height * 3, 30, self.colors["green"], True)
        self.draw_text("[S] Settings", W // 2, menu_start_y + line_height * 4, 30, self.colors["cyan"], True)
        
        self.draw_text("[ESC] Quit", W // 2, menu_start_y + line_height * 6, 24, self.colors["yellow"], True)

        # Status bar at bottom
        status_y = H - 90
        
        # Device status
        device_icon = "🔧" if model.is_dummy_device else "🧠"
        device_color = self.colors["yellow"] if model.is_dummy_device else self.colors["green"]
        self.draw_text(
            f"Device: {device_icon} {model.device_name}",
            W // 2,
            status_y,
            18,
            device_color,
            True,
        )

        # Model status
        model_status = model.get_model_status()
        model_color = (
            self.colors["green"] if model_status["exists"] else self.colors["red"]
        )
        self.draw_text(
            f"Model: {model_status['status']}",
            W // 2,
            status_y + 25,
            18,
            model_color,
            True,
        )
        
        # Source info
        source_info = model.source_info
        if source_info["sample_rate"]:
            self.draw_text(
                f"{source_info['sample_rate']}Hz · {source_info['channels']} channels",
                W // 2,
                status_y + 50,
                14,
                self.colors["light_grey"],
                True,
            )
