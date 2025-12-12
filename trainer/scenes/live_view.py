"""View for LiveScene - handles all rendering for live BCI to MQTT."""

import pygame as pg
import time


class LiveView:
    """View for LiveScene - handles rendering only, no state modification."""

    def __init__(self, screen):
        self.screen = screen
        self.colors = {
            "white": (255, 255, 255),
            "grey": (40, 40, 40),
            "green": (0, 200, 0),
            "red": (200, 60, 60),
            "yellow": (220, 200, 0),
            "blue": (0, 120, 220),
            "cyan": (0, 180, 180),
            "orange": (220, 140, 0),
            "purple": (140, 80, 200),
            "dark_bg": (15, 15, 18),
            "light_grey": (100, 100, 100),
            "darker_grey": (60, 60, 60),
            "dark_green": (0, 80, 0),
        }
        
        # Direction colors
        self.direction_colors = {
            "forward": self.colors["green"],
            "backward": self.colors["red"],
            "left": self.colors["blue"],
            "right": self.colors["orange"],
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
        """Main render method."""
        if model.is_running:
            self.render_running(model)
        else:
            self.render_config(model)

    def render_config(self, model):
        """Render configuration screen."""
        W, H = self.screen.get_size()
        self.screen.fill(self.colors["dark_bg"])

        # Title
        self.draw_text("Live BCI → MQTT", W // 2, 35, 36, self.colors["white"], True)
        self.draw_text(
            "Real-time EEG prediction to MQTT",
            W // 2, 70, 18, self.colors["light_grey"], True
        )

        # Status indicators
        status_y = 110
        
        # Model status
        model_color = self.colors["green"] if model.model_loaded else self.colors["red"]
        model_status = "✓ Loaded" if model.model_loaded else "✗ Not loaded"
        self.draw_text(f"ML Model: {model_status}", 60, status_y, 20, model_color)
        
        # Source status
        source_color = self.colors["green"] if model.source_connected else self.colors["red"]
        source_status = "✓ Connected" if model.source_connected else "✗ Not connected"
        self.draw_text(f"EEG Source: {source_status}", 60, status_y + 28, 20, source_color)
        
        # MQTT status
        mqtt_color = self.colors["green"] if model.mqtt_connected else self.colors["yellow"]
        mqtt_status = "✓ Connected" if model.mqtt_connected else "○ Not connected"
        self.draw_text(f"MQTT: {mqtt_status}", 60, status_y + 56, 20, mqtt_color)
        
        if model.mqtt_error:
            self.draw_text(f"  Error: {model.mqtt_error[:50]}", 60, status_y + 80, 16, self.colors["red"])

        # Configuration section
        config_y = 230
        self.draw_text("MQTT Configuration:", W // 2, config_y, 24, self.colors["yellow"], True)
        
        # Editable fields
        fields = [
            ("broker", "Broker", model.mqtt_broker, "[1]"),
            ("port", "Port", str(model.mqtt_port), "[2]"),
            ("topic", "Topic", model.mqtt_topic, "[3]"),
            ("threshold", "Confidence", f"{model.confidence_threshold:.2f}", "[4]"),
        ]
        
        field_y = config_y + 35
        for field_id, label, value, key in fields:
            is_editing = model.editing_field == field_id
            
            if is_editing:
                # Editing mode
                display_value = model.edit_buffer + "█"
                color = self.colors["cyan"]
                bg_rect = pg.Rect(180, field_y - 3, 300, 26)
                pg.draw.rect(self.screen, self.colors["darker_grey"], bg_rect)
            else:
                display_value = value
                color = self.colors["white"]
            
            self.draw_text(f"{key} {label}:", 80, field_y, 18, self.colors["light_grey"])
            self.draw_text(display_value, 220, field_y, 18, color)
            field_y += 30

        # Instructions
        instructions_y = H - 140
        
        if model.editing_field:
            self.draw_text(
                "Type to edit, [ENTER] confirm, [ESC] cancel",
                W // 2, instructions_y, 18, self.colors["cyan"], True
            )
        else:
            self.draw_text(
                "[1-4] Edit fields    [C] Connect MQTT    [ENTER] Start",
                W // 2, instructions_y, 18, self.colors["white"], True
            )
        
        # Start button highlight
        can_start = model.model_loaded and model.source_connected
        start_color = self.colors["green"] if can_start else self.colors["darker_grey"]
        start_text = "[ENTER] Start Live Session" if can_start else "Load model and connect source first"
        self.draw_text(start_text, W // 2, instructions_y + 40, 22, start_color, True)
        
        self.draw_text("[ESC] Back to menu", W // 2, H - 50, 18, self.colors["yellow"], True)

    def render_running(self, model):
        """Render running session screen."""
        W, H = self.screen.get_size()
        self.screen.fill(self.colors["dark_bg"])

        # Title with live indicator
        pulse = int(time.time() * 2) % 2 == 0
        live_color = self.colors["red"] if pulse else self.colors["dark_green"]
        self.draw_text("● LIVE", 60, 25, 28, live_color)
        self.draw_text("BCI → MQTT", 140, 30, 24, self.colors["white"])

        # Connection status bar
        status_text = f"MQTT: {model.mqtt_broker}:{model.mqtt_port} → {model.mqtt_topic}"
        status_color = self.colors["green"] if model.mqtt_connected else self.colors["red"]
        self.draw_text(status_text, W - 60, 30, 16, status_color, False)
        # Right align by calculating width
        font = pg.font.SysFont("Arial", 16)
        text_width = font.size(status_text)[0]
        self.screen.fill(self.colors["dark_bg"], (W - 60, 20, 200, 30))  # Clear area
        self.draw_text(status_text, W - text_width - 20, 30, 16, status_color)

        # Current prediction - large display
        pred_y = 100
        self.draw_text("Current Direction:", W // 2, pred_y, 20, self.colors["light_grey"], True)
        
        if model.current_direction:
            dir_color = self.direction_colors.get(model.current_direction, self.colors["white"])
            self.draw_text(
                model.current_direction.upper(),
                W // 2, pred_y + 50, 56, dir_color, True
            )
            
            # Confidence bar
            bar_width = 300
            bar_height = 20
            bar_x = (W - bar_width) // 2
            bar_y = pred_y + 100
            
            # Background
            pg.draw.rect(self.screen, self.colors["darker_grey"], (bar_x, bar_y, bar_width, bar_height))
            # Fill
            fill_width = int(bar_width * model.current_confidence)
            fill_color = self.colors["green"] if model.current_confidence >= model.confidence_threshold else self.colors["orange"]
            pg.draw.rect(self.screen, fill_color, (bar_x, bar_y, fill_width, bar_height))
            # Border
            pg.draw.rect(self.screen, self.colors["light_grey"], (bar_x, bar_y, bar_width, bar_height), 2)
            
            self.draw_text(
                f"{model.current_confidence:.1%}",
                W // 2, bar_y + bar_height + 15, 18, self.colors["white"], True
            )
        else:
            self.draw_text("Waiting...", W // 2, pred_y + 50, 40, self.colors["light_grey"], True)

        # Direction visualization - arrow pad
        pad_x = W // 2
        pad_y = 320
        pad_size = 50
        
        directions = [
            ("forward", pad_x, pad_y - pad_size, "▲"),
            ("backward", pad_x, pad_y + pad_size, "▼"),
            ("left", pad_x - pad_size * 1.5, pad_y, "◄"),
            ("right", pad_x + pad_size * 1.5, pad_y, "►"),
        ]
        
        for direction, dx, dy, symbol in directions:
            is_active = model.current_direction == direction
            color = self.direction_colors[direction] if is_active else self.colors["darker_grey"]
            size = 36 if is_active else 28
            self.draw_text(symbol, int(dx), int(dy), size, color, True)

        # Statistics panel
        stats_y = 420
        self.draw_text("Session Statistics:", 60, stats_y, 18, self.colors["yellow"])
        
        duration = model.get_session_duration()
        mins, secs = divmod(int(duration), 60)
        self.draw_text(f"Duration: {mins:02d}:{secs:02d}", 60, stats_y + 25, 16, self.colors["white"])
        self.draw_text(f"Predictions: {model.predictions_count}", 60, stats_y + 45, 16, self.colors["white"])
        self.draw_text(f"Published: {model.messages_published}", 60, stats_y + 65, 16, self.colors["green"])
        self.draw_text(f"Rate: {model.get_predictions_per_second():.1f}/s", 60, stats_y + 85, 16, self.colors["white"])

        # Direction counts
        counts_x = W - 200
        self.draw_text("Direction Counts:", counts_x, stats_y, 18, self.colors["yellow"])
        for i, (direction, count) in enumerate(model.direction_counts.items()):
            color = self.direction_colors.get(direction, self.colors["white"])
            self.draw_text(f"{direction}: {count}", counts_x, stats_y + 25 + i * 20, 16, color)

        # Recent predictions
        history_y = stats_y
        history_x = W // 2 - 50
        self.draw_text("Recent:", history_x, history_y, 18, self.colors["yellow"])
        
        for i, record in enumerate(list(model.prediction_history)[-5:]):
            age = time.time() - record.timestamp
            alpha = max(0.3, min(1.0, 1.0 - age / 5.0))
            color = self.direction_colors.get(record.direction, self.colors["white"])
            # Simulate alpha with darker color - clamp values to valid RGB range
            faded_color = tuple(max(0, min(255, int(c * alpha))) for c in color)
            pub_indicator = "→" if record.published else "○"
            text = f"{pub_indicator} {record.direction}"
            if record.confidence is not None:
                text += f" ({record.confidence:.0%})"
            self.draw_text(text, history_x, history_y + 25 + i * 18, 14, faded_color)

        # Controls
        self.draw_text(
            "[SPACE] Stop    [ESC] Back to menu",
            W // 2, H - 40, 18, self.colors["yellow"], True
        )

