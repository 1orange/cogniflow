"""View for CalibrationScene - handles all rendering."""

import pygame as pg


class CalibrationView:
    """View for CalibrationScene - handles rendering only, no state modification."""

    def __init__(self, screen):
        self.screen = screen
        self.colors = {
            "white": (255, 255, 255),
            "grey": (40, 40, 40),
            "yellow": (220, 200, 0),
            "blue": (0, 120, 220),
            "green": (0, 200, 0),
            "red": (200, 60, 60),
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
                    (size * 0.2, c),
                    (size * 0.5, size * 0.25),
                    (size * 0.5, size * 0.4),
                    (size * 0.8, size * 0.4),
                    (size * 0.8, size * 0.6),
                    (size * 0.5, size * 0.6),
                    (size * 0.5, size * 0.75),
                ],
            )
        elif direction == "right":
            pg.draw.polygon(
                surf,
                color,
                [
                    (size * 0.8, c),
                    (size * 0.5, size * 0.25),
                    (size * 0.5, size * 0.4),
                    (size * 0.2, size * 0.4),
                    (size * 0.2, size * 0.6),
                    (size * 0.5, size * 0.6),
                    (size * 0.5, size * 0.75),
                ],
            )
        elif direction == "forward":
            pg.draw.polygon(
                surf,
                color,
                [
                    (c, size * 0.2),
                    (size * 0.25, size * 0.5),
                    (size * 0.4, size * 0.5),
                    (size * 0.4, size * 0.8),
                    (size * 0.6, size * 0.8),
                    (size * 0.6, size * 0.5),
                    (size * 0.75, size * 0.5),
                ],
            )
        elif direction == "backward":
            pg.draw.polygon(
                surf,
                color,
                [
                    (c, size * 0.8),
                    (size * 0.25, size * 0.5),
                    (size * 0.4, size * 0.5),
                    (size * 0.4, size * 0.2),
                    (size * 0.6, size * 0.2),
                    (size * 0.6, size * 0.5),
                    (size * 0.75, size * 0.5),
                ],
            )
        return surf

    def render_calibration(self, model, elapsed, remaining, total):
        """Render the calibration screen."""
        W, H = self.screen.get_size()
        self.screen.fill(self.colors["grey"])

        # Title
        self.draw_text("Calibration", W // 2, 40, 40, self.colors["white"], True)

        # Trial info
        trial_info = model.get_current_trial_info()
        self.draw_text(
            f"Trial {trial_info['trial_num']}/{trial_info['total_trials']} | Label: {trial_info['intended']}",
            W // 2,
            90,
            28,
            self.colors["yellow"],
            True,
        )

        # Progress bar
        pg.draw.rect(
            self.screen, self.colors["white"], (W * 0.2, H * 0.9, W * 0.6, 10), 1
        )
        progress_color = (
            self.colors["blue"] if model.phase == "task" else self.colors["white"]
        )
        pg.draw.rect(
            self.screen,
            progress_color,
            (W * 0.2, H * 0.9, W * 0.6 * (1 - remaining / total), 10),
        )

        # Arrow for task phase
        if model.phase == "task":
            arrow_surf = self.arrow_surface(
                trial_info["intended"], 160, self.colors["white"]
            )
            self.screen.blit(arrow_surf, (W // 2 - 80, H // 2 - 80))

    def render_training(self, model):
        """Render training screen."""
        W, H = self.screen.get_size()
        self.screen.fill(self.colors["grey"])

        import time

        dots = "." * (int(time.time() * 2) % 4)
        self.draw_text(
            "Training model" + dots, W // 2, H // 2, 36, self.colors["yellow"], True
        )
        self.draw_text(
            "Please wait", W // 2, H // 2 + 40, 24, self.colors["white"], True
        )

    def render_complete(self, model):
        """Render completion screen."""
        W, H = self.screen.get_size()
        self.screen.fill(self.colors["grey"])

        self.draw_text(
            "Training complete", W // 2, H // 2 - 40, 36, self.colors["green"], True
        )

        if model.training_error:
            self.draw_text(
                f"Error: {model.training_error}",
                W // 2,
                H // 2 + 10,
                28,
                self.colors["red"],
                True,
            )
        elif model.balanced_accuracy is not None:
            self.draw_text(
                f"Hold-out balanced acc: {model.balanced_accuracy:.2f}",
                W // 2,
                H // 2 + 10,
                28,
                self.colors["white"],
                True,
            )

        self.draw_text(
            "Press ESC to return", W // 2, H // 2 + 60, 24, self.colors["yellow"], True
        )
