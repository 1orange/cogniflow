"""Controller for SettingsScene - handles user input."""

import pygame as pg


class SettingsController:
    """Handles keyboard input for settings scene."""

    def __init__(self, model):
        self.model = model

    def handle_keydown(self, key) -> str:
        """
        Handle keydown event.
        
        Args:
            key: pygame key constant
            
        Returns:
            Action string: 'quit', 'select', 'refresh', 'none'
        """
        if key == pg.K_ESCAPE:
            return "quit"
        elif key == pg.K_UP:
            self.model.move_selection(-1)
            return "none"
        elif key == pg.K_DOWN:
            self.model.move_selection(1)
            return "none"
        elif key == pg.K_RETURN or key == pg.K_KP_ENTER:
            return "select"
        elif key == pg.K_r:
            return "refresh"
        return "none"

