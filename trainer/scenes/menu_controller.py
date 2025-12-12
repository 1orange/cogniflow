"""Controller for MenuScene - handles input events and updates model."""

import pygame as pg
import os
from trainer.model_store import model_store


class MenuController:
    """Controller for MenuScene - maps input to model updates."""

    def __init__(self, model):
        self.model = model

    def handle_keydown(self, key):
        """
        Handle keydown events.

        Args:
            key: pygame key constant

        Returns:
            str: Action to take ('calibrate', 'record', 'modulus', 'live', 'drive_bci', 'drive_arrow', 'quit', 'none')
        """
        match key:
            case pg.K_ESCAPE:
                return "quit"
            case pg.K_c:
                return "calibrate"
            case pg.K_r:
                return "record"
            case pg.K_d:
                # Check model store first, then file
                if model_store.has_model or os.path.exists(self.model.model_path):
                    return "drive_bci"
                else:
                    return "drive_bci_no_model"
            case pg.K_a:
                return "drive_arrow"
            case pg.K_m:
                return "modulus"
            case pg.K_l:
                return "live"
            case _:
                return "none"
