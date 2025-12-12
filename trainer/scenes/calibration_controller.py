"""Controller for CalibrationScene - handles input events and coordinates calibration."""

import pygame as pg
import time
from config import BASELINE_SEC, TASK_SEC, REST_SEC


class CalibrationController:
    """Controller for CalibrationScene - coordinates calibration process."""

    def __init__(self, model, source):
        self.model = model
        self.source = source
        self.phase_start_time = None

    def start(self):
        """Start calibration process."""
        import time

        self.model.phase_start_time = time.time()
        self.phase_start_time = self.model.phase_start_time
        self.source.start()
        if hasattr(self.source, "set_intended_label"):
            self.source.set_intended_label(None)

    def stop(self):
        """Stop calibration process."""
        self.source.stop()

    def handle_keydown(self, key):
        """
        Handle keydown events.

        Args:
            key: pygame key constant

        Returns:
            str: Action to take ('quit', 'none')
        """
        if key == pg.K_ESCAPE:
            return "quit"
        return "none"

    def update_phase_timing(self):
        """Update phase timing and advance phases as needed."""
        if self.phase_start_time is None:
            self.phase_start_time = time.time()
            self.model.phase_start_time = self.phase_start_time

        elapsed = time.time() - self.phase_start_time

        if self.model.phase == "baseline":
            total = BASELINE_SEC
        elif self.model.phase == "task":
            total = TASK_SEC
        else:  # rest
            total = REST_SEC

        remaining = max(0.0, total - elapsed)

        if remaining <= 1e-3:
            # Advance phase
            if hasattr(self.source, "set_intended_label"):
                if self.model.phase == "task":
                    self.source.set_intended_label(self.model.intended)
                else:
                    self.source.set_intended_label(None)

            if not self.model.advance_phase():
                return False, elapsed, remaining, total  # All trials complete

            self.phase_start_time = time.time()
            self.model.phase_start_time = self.phase_start_time
            elapsed = 0.0
            remaining = total

        return True, elapsed, remaining, total

    def update_source_label(self):
        """Update source intended label based on current phase."""
        if hasattr(self.source, "set_intended_label"):
            if self.model.phase == "task":
                self.source.set_intended_label(self.model.intended)
            else:
                self.source.set_intended_label(None)
