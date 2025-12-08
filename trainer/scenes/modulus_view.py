"""View for ModulusScene - handles all rendering."""

import pygame as pg


class ModulusView:
    """View for ModulusScene - handles rendering only, no state modification."""

    def __init__(self, screen):
        self.screen = screen
        self.colors = {
            "white": (255, 255, 255),
            "grey": (40, 40, 40),
            "green": (0, 200, 0),
            "red": (200, 60, 60),
            "yellow": (220, 200, 0),
            "blue": (0, 120, 220),
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

    def render_menu(self, model):
        """Render the experiment configuration menu."""
        W, H = self.screen.get_size()
        self.screen.fill(self.colors["dark_bg"])

        # Title
        self.draw_text(
            "Modulus Preprocessing Experiments",
            W // 2,
            40,
            40,
            self.colors["white"],
            True,
        )

        # Experiment Mode Selection
        self.draw_text("Experiment Mode:", W // 2, 100, 28, self.colors["yellow"], True)

        y_offset = 140
        mode_labels = {
            "binary": "Binary (Forward vs Rest)",
            "multiclass": "Multiclass (4 Directions)",
            "both": "Both (Binary + Multiclass)",
        }

        for i, mode in enumerate(model.experiment_modes):
            color = (
                self.colors["green"]
                if i == model.selected_mode_index
                else self.colors["light_grey"]
            )
            prefix = "> " if i == model.selected_mode_index else "  "
            label = mode_labels.get(mode, mode.capitalize())
            self.draw_text(
                f"{prefix}{label}",
                W // 2,
                y_offset + i * 35,
                24,
                color,
                True,
            )

        # Options
        options_y = y_offset + len(model.experiment_modes) * 35 + 30
        self.draw_text("Options:", W // 2, options_y, 28, self.colors["yellow"], True)

        # Quick Mode
        quick_color = (
            self.colors["green"] if model.quick_mode else self.colors["light_grey"]
        )
        quick_prefix = "[X] " if model.quick_mode else "[ ] "
        self.draw_text(
            f"{quick_prefix}Quick Mode (faster, fewer experiments)",
            W // 2,
            options_y + 35,
            22,
            quick_color,
            True,
        )

        # Hyperparameter Tuning
        tuning_color = (
            self.colors["green"]
            if model.hyperparameter_tuning
            else self.colors["light_grey"]
        )
        tuning_prefix = "[X] " if model.hyperparameter_tuning else "[ ] "
        self.draw_text(
            f"{tuning_prefix}Hyperparameter Tuning",
            W // 2,
            options_y + 60,
            22,
            tuning_color,
            True,
        )

        # Controls
        controls_y = H - 180
        self.draw_text(
            "[UP/DOWN] Select mode",
            W // 2,
            controls_y,
            22,
            self.colors["white"],
            True,
        )
        self.draw_text(
            "[Q] Toggle Quick Mode  [H] Toggle Hyperparameter Tuning",
            W // 2,
            controls_y + 25,
            20,
            self.colors["white"],
            True,
        )
        self.draw_text(
            "[ENTER] Run experiments",
            W // 2,
            controls_y + 50,
            24,
            self.colors["green"],
            True,
        )
        self.draw_text(
            "[ESC] Back to menu",
            W // 2,
            controls_y + 80,
            22,
            self.colors["yellow"],
            True,
        )

    def render_running(self, model):
        """Render pipeline execution screen."""
        W, H = self.screen.get_size()
        self.screen.fill(self.colors["dark_bg"])

        # Title
        self.draw_text(
            "Running ML Pipeline", W // 2, 100, 40, self.colors["white"], True
        )

        # Current step
        if model.current_step:
            self.draw_text(
                model.current_step, W // 2, H // 2, 32, self.colors["green"], True
            )

        # Loading indicator
        import time

        dots = "." * (int(time.time() * 2) % 4)
        self.draw_text(
            f"Processing{dots}", W // 2, H // 2 + 60, 24, self.colors["yellow"], True
        )

        # Instructions
        self.draw_text(
            "[ESC] Cancel (may take a moment)",
            W // 2,
            H - 100,
            20,
            self.colors["light_grey"],
            True,
        )

    def render_complete(self, model):
        """Render pipeline completion screen."""
        W, H = self.screen.get_size()
        self.screen.fill(self.colors["dark_bg"])

        # Title
        self.draw_text(
            "Pipeline Complete!", W // 2, 100, 40, self.colors["green"], True
        )

        # Results summary
        y_offset = 200
        if model.results_path:
            self.draw_text(
                "Results saved to:",
                W // 2,
                y_offset,
                24,
                self.colors["white"],
                True,
            )
            self.draw_text(
                model.results_path,
                W // 2,
                y_offset + 30,
                20,
                self.colors["green"],
                True,
            )
            y_offset += 70

        if model.results_summary:
            for line in model.results_summary.split("\n"):
                if line.strip() and len(line.strip()) < 80:
                    self.draw_text(
                        line.strip(), W // 2, y_offset, 20, self.colors["white"], True
                    )
                    y_offset += 25
                    if y_offset > H - 150:
                        break

        # Instructions
        self.draw_text(
            "[ESC] Back to menu",
            W // 2,
            H - 100,
            28,
            self.colors["yellow"],
            True,
        )

    def render_error(self, model):
        """Render error screen."""
        W, H = self.screen.get_size()
        self.screen.fill(self.colors["dark_bg"])

        # Title
        self.draw_text("Error", W // 2, 100, 40, self.colors["red"], True)

        # Error message
        if model.error_message:
            # Wrap long error messages
            words = model.error_message.split()
            lines = []
            current_line = ""
            for word in words:
                test_line = current_line + " " + word if current_line else word
                if len(test_line) < 60:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)

            y_offset = 200
            for line in lines[:10]:  # Limit to 10 lines
                self.draw_text(line, W // 2, y_offset, 20, self.colors["white"], True)
                y_offset += 25

        # Instructions
        self.draw_text(
            "[ESC] Back to menu",
            W // 2,
            H - 100,
            28,
            self.colors["yellow"],
            True,
        )
