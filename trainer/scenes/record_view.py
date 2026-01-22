"""View for RecordScene - handles all rendering."""

import pygame as pg
from bci.utils import LABELS


class RecordView:
    """View for RecordScene - handles rendering only, no state modification."""

    def __init__(self, screen):
        self.screen = screen
        self.colors = {
            "white": (255, 255, 255),
            "grey": (40, 40, 40),
            "yellow": (220, 200, 0),
            "blue": (0, 120, 220),
            "green": (0, 200, 0),
            "red": (200, 60, 60),
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

    def render_select_directions(self, model):
        """Render direction selection screen."""
        W, H = self.screen.get_size()
        self.screen.fill(self.colors["grey"])

        self.draw_text(
            "Select Directions to Record", W // 2, 60, 40, self.colors["white"], True
        )
        self.draw_text(
            "Press 1-4 to toggle directions",
            W // 2,
            110,
            24,
            self.colors["yellow"],
            True,
        )
        self.draw_text(
            "Press ENTER to continue or ESC to cancel",
            W // 2,
            140,
            20,
            self.colors["white"],
            True,
        )

        y_start = 200
        y_spacing = 80

        for i, label in enumerate(LABELS):
            y = y_start + i * y_spacing
            color = (
                self.colors["green"]
                if model.selected_directions[label]
                else self.colors["red"]
            )
            status = "✓" if model.selected_directions[label] else "✗"
            self.draw_text(
                f"[{i + 1}] {status} {label.upper()}", W // 2, y, 32, color, True
            )

        selected_count = sum(model.selected_directions.values())
        self.draw_text(
            f"Selected: {selected_count}/{len(LABELS)}",
            W // 2,
            H - 80,
            24,
            self.colors["yellow"],
            True,
        )

    def render_select_window(self, model):
        """Render window duration selection screen."""
        W, H = self.screen.get_size()
        self.screen.fill(self.colors["grey"])

        self.draw_text(
            "Set Recording Window Duration", W // 2, 60, 40, self.colors["white"], True
        )
        self.draw_text(
            "How long should each trial last?",
            W // 2,
            110,
            24,
            self.colors["yellow"],
            True,
        )

        self.draw_text(
            f"Duration: {model.window_duration:.1f} seconds",
            W // 2,
            H // 2 - 40,
            48,
            self.colors["green"],
            True,
        )

        self.draw_text(
            "Use UP/DOWN arrows to adjust (0.5s steps)",
            W // 2,
            H // 2 + 40,
            24,
            self.colors["white"],
            True,
        )
        self.draw_text(
            "Use LEFT/RIGHT arrows for fine adjustment (0.1s steps)",
            W // 2,
            H // 2 + 70,
            20,
            self.colors["white"],
            True,
        )
        self.draw_text(
            "Press ENTER to continue or ESC to cancel",
            W // 2,
            H // 2 + 110,
            20,
            self.colors["yellow"],
            True,
        )

    def render_select_trials(self, model):
        """Render trials count selection screen."""
        W, H = self.screen.get_size()
        self.screen.fill(self.colors["grey"])

        self.draw_text(
            "Set Number of Trials", W // 2, 60, 40, self.colors["white"], True
        )
        self.draw_text(
            "How many trials per direction?",
            W // 2,
            110,
            24,
            self.colors["yellow"],
            True,
        )

        self.draw_text(
            f"Trials: {model.trials_per_direction}",
            W // 2,
            H // 2 - 40,
            48,
            self.colors["green"],
            True,
        )

        self.draw_text(
            "Use UP/DOWN arrows to adjust",
            W // 2,
            H // 2 + 40,
            24,
            self.colors["white"],
            True,
        )
        self.draw_text(
            "Press ENTER to continue or ESC to cancel",
            W // 2,
            H // 2 + 80,
            20,
            self.colors["yellow"],
            True,
        )

    def render_recording(self, model, elapsed, remaining, total):
        """Render recording screen."""
        W, H = self.screen.get_size()
        self.screen.fill(self.colors["grey"])

        self.draw_text("Data Recording", W // 2, 40, 40, self.colors["white"], True)

        trial_info = model.get_current_trial_info()
        self.draw_text(
            f"Trial {trial_info['trial_num']}/{trial_info['total_trials']} | Direction: {trial_info['intended']}",
            W // 2,
            90,
            28,
            self.colors["yellow"],
            True,
        )

        phase_text = trial_info["phase"].upper()
        phase_color = (
            self.colors["blue"]
            if trial_info["phase"] == "task"
            else self.colors["white"]
        )
        self.draw_text(f"Phase: {phase_text}", W // 2, 130, 32, phase_color, True)

        # Progress bar
        pg.draw.rect(
            self.screen, self.colors["white"], (W * 0.2, H * 0.9, W * 0.6, 10), 1
        )
        progress_color = (
            self.colors["blue"]
            if trial_info["phase"] == "task"
            else self.colors["white"]
        )
        pg.draw.rect(
            self.screen,
            progress_color,
            (W * 0.2, H * 0.9, W * 0.6 * (1 - remaining / total), 10),
        )

        if trial_info["phase"] == "task":
            arrow_surf = self.arrow_surface(
                trial_info["intended"], 160, self.colors["white"]
            )
            self.screen.blit(arrow_surf, (W // 2 - 80, H // 2 - 80))

    def render_saving(self, model):
        """Render saving screen."""
        W, H = self.screen.get_size()
        self.screen.fill(self.colors["grey"])

        import time

        dots = "." * (int(time.time() * 2) % 4)
        self.draw_text(
            "Saving data" + dots, W // 2, H // 2, 36, self.colors["yellow"], True
        )
        self.draw_text(
            "Please wait", W // 2, H // 2 + 40, 24, self.colors["white"], True
        )

    def render_complete(self, model):
        """Render completion screen."""
        W, H = self.screen.get_size()
        self.screen.fill(self.colors["grey"])

        if model.saving_success:
            self.draw_text(
                "Data recording complete",
                W // 2,
                H // 2 - 40,
                36,
                self.colors["green"],
                True,
            )
            self.draw_text(
                "Raw data saved to /data folder",
                W // 2,
                H // 2 + 10,
                28,
                self.colors["white"],
                True,
            )

            total_windows = sum(
                len(model.recorded_data.get(direction, []))
                for direction in model.get_selected_directions_list()
            )
            self.draw_text(
                f"Total windows recorded: {total_windows}",
                W // 2,
                H // 2 + 50,
                24,
                self.colors["white"],
                True,
            )
        else:
            self.draw_text(
                "Error saving data", W // 2, H // 2 - 40, 36, self.colors["red"], True
            )
            if model.saving_error:
                self.draw_text(
                    model.saving_error[:50],
                    W // 2,
                    H // 2 + 10,
                    24,
                    self.colors["white"],
                    True,
                )

        self.draw_text(
            "Press ESC to return", W // 2, H // 2 + 100, 24, self.colors["yellow"], True
        )
