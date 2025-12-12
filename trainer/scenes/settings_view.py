"""View for SettingsScene - renders device selection UI."""

import pygame as pg
from bci.devices import DeviceType


class SettingsView:
    """Renders the settings/device selection interface."""

    def __init__(self, screen):
        self.screen = screen
        self.colors = {
            "white": (255, 255, 255),
            "green": (0, 200, 100),
            "red": (220, 80, 80),
            "yellow": (220, 200, 60),
            "blue": (80, 140, 220),
            "cyan": (80, 200, 200),
            "dark_bg": (18, 18, 22),
            "card_bg": (30, 30, 38),
            "card_selected": (45, 45, 58),
            "card_active": (35, 55, 45),
            "grey": (120, 120, 130),
            "light_grey": (180, 180, 190),
        }
        
    def draw_text(self, text, x, y, size=24, color=None, center=False):
        """Draw text on screen."""
        if color is None:
            color = self.colors["white"]
        font = pg.font.SysFont("Segoe UI", size)
        img = font.render(str(text), True, color)
        rect = img.get_rect()
        if center:
            rect.center = (x, y)
        else:
            rect.topleft = (x, y)
        self.screen.blit(img, rect)
        return rect

    def render(self, model):
        """Render the settings screen."""
        W, H = self.screen.get_size()
        self.screen.fill(self.colors["dark_bg"])
        
        # Title
        self.draw_text("⚙️ Device Settings", W // 2, 50, 42, self.colors["white"], True)
        
        # Current device status
        current_text = f"Current: {model.current_device.name}" if model.current_device else "Current: None"
        current_color = self.colors["green"] if model.current_device else self.colors["grey"]
        self.draw_text(current_text, W // 2, 100, 24, current_color, True)
        
        # Device list
        list_y = 160
        list_x = W // 2 - 300
        list_width = 600
        item_height = 70
        
        self.draw_text("Available Devices:", list_x, list_y - 35, 20, self.colors["yellow"])
        
        if not model.available_devices:
            self.draw_text(
                "No devices found. Press [R] to refresh.",
                W // 2, list_y + 50, 22, self.colors["grey"], True
            )
        else:
            for i, device in enumerate(model.available_devices):
                y = list_y + i * (item_height + 8)
                
                # Skip if off screen
                if y > H - 180:
                    more_count = len(model.available_devices) - i
                    self.draw_text(
                        f"... and {more_count} more (scroll with arrows)",
                        W // 2, y, 18, self.colors["grey"], True
                    )
                    break
                
                self._render_device_card(
                    device, list_x, y, list_width, item_height,
                    selected=(i == model.selected_index),
                    active=model.is_device_active(device)
                )
        
        # Status/Error message
        status_y = H - 120
        if model.error_message:
            self.draw_text(model.error_message, W // 2, status_y, 22, self.colors["red"], True)
        elif model.status_message:
            self.draw_text(model.status_message, W // 2, status_y, 20, self.colors["grey"], True)
        
        # Controls
        controls_y = H - 70
        controls = [
            ("[↑/↓]", "Select"),
            ("[ENTER]", "Connect"),
            ("[R]", "Refresh"),
            ("[ESC]", "Back"),
        ]
        
        total_width = sum(len(key) + len(desc) for key, desc in controls) * 10 + len(controls) * 40
        x = (W - total_width) // 2
        
        for key, desc in controls:
            key_rect = self.draw_text(key, x, controls_y, 20, self.colors["cyan"])
            x = key_rect.right + 8
            desc_rect = self.draw_text(desc, x, controls_y, 20, self.colors["grey"])
            x = desc_rect.right + 30
            
    def _render_device_card(self, device, x, y, width, height, selected=False, active=False):
        """Render a single device card."""
        # Background
        if active:
            bg_color = self.colors["card_active"]
        elif selected:
            bg_color = self.colors["card_selected"]
        else:
            bg_color = self.colors["card_bg"]
            
        rect = pg.Rect(x, y, width, height)
        pg.draw.rect(self.screen, bg_color, rect, border_radius=8)
        
        # Selection border
        if selected:
            pg.draw.rect(self.screen, self.colors["cyan"], rect, width=2, border_radius=8)
        elif active:
            pg.draw.rect(self.screen, self.colors["green"], rect, width=2, border_radius=8)
        
        # Device icon
        icon = "🔧" if device.device_type == DeviceType.DUMMY else "🧠"
        self.draw_text(icon, x + 25, y + height // 2, 28, self.colors["white"], True)
        
        # Device name
        name_color = self.colors["white"]
        self.draw_text(device.name, x + 60, y + 15, 22, name_color)
        
        # Description
        self.draw_text(device.description, x + 60, y + 42, 16, self.colors["grey"])
        
        # Status indicator
        if active:
            status_text = "● ACTIVE"
            status_color = self.colors["green"]
        elif device.available:
            status_text = "○ Available"
            status_color = self.colors["light_grey"]
        else:
            status_text = "✗ Unavailable"
            status_color = self.colors["red"]
            
        self.draw_text(status_text, x + width - 120, y + height // 2, 16, status_color, True)

