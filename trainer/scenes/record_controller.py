"""Controller for RecordScene - handles input events and coordinates recording."""

import pygame as pg
import time
import os
import numpy as np
from config import BASELINE_SEC, REST_SEC


class RecordController:
    """Controller for RecordScene - coordinates recording process."""

    def __init__(self, model, source):
        self.model = model
        self.source = source
        self.phase_start_time = None

    def handle_keydown(self, key, step):
        """
        Handle keydown events based on current wizard step.

        Args:
            key: pygame key constant
            step: current wizard step

        Returns:
            str: Action to take
        """
        if key == pg.K_ESCAPE:
            return "cancel"

        if step == "select_directions":
            if key == pg.K_RETURN:
                if self.model.get_selected_directions_list():
                    return "continue"
            elif pg.K_1 <= key <= pg.K_4:
                index = key - pg.K_1
                self.model.toggle_direction(index)
                return "none"

        elif step == "select_window":
            if key == pg.K_RETURN:
                return "continue"
            elif key == pg.K_UP:
                self.model.window_duration = min(20.0, self.model.window_duration + 0.5)
                return "none"
            elif key == pg.K_DOWN:
                self.model.window_duration = max(1.0, self.model.window_duration - 0.5)
                return "none"
            elif key == pg.K_RIGHT:
                self.model.window_duration = min(20.0, self.model.window_duration + 0.1)
                return "none"
            elif key == pg.K_LEFT:
                self.model.window_duration = max(1.0, self.model.window_duration - 0.1)
                return "none"

        elif step == "select_trials":
            if key == pg.K_RETURN:
                return "continue"
            elif key == pg.K_UP:
                self.model.trials_per_direction = min(
                    50, self.model.trials_per_direction + 1
                )
                return "none"
            elif key == pg.K_DOWN:
                self.model.trials_per_direction = max(
                    1, self.model.trials_per_direction - 1
                )
                return "none"

        elif step == "complete":
            if key == pg.K_ESCAPE:
                return "quit"

        return "none"

    def start_recording(self):
        """Start recording process."""
        self.model.initialize_recording()
        self.phase_start_time = time.time()
        self.model.phase_start_time = self.phase_start_time
        self.source.start()
        if hasattr(self.source, "set_intended_label"):
            self.source.set_intended_label(None)

    def stop_recording(self):
        """Stop recording process."""
        self.source.stop()

    def update_phase_timing(self):
        """Update phase timing and advance phases as needed."""
        if self.phase_start_time is None:
            self.phase_start_time = time.time()
            self.model.phase_start_time = self.phase_start_time

        elapsed = time.time() - self.phase_start_time

        if self.model.phase == "baseline":
            total = BASELINE_SEC
        elif self.model.phase == "task":
            total = self.model.window_duration
        else:  # rest
            total = REST_SEC

        remaining = max(0.0, total - elapsed)

        if remaining <= 1e-3:
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

    def save_data(self):
        """Save recorded data to files."""
        try:
            os.makedirs("data", exist_ok=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")

            for direction in self.model.get_selected_directions_list():
                if self.model.recorded_data.get(direction):
                    data_array = np.array(self.model.recorded_data[direction])
                    filename = f"data/recorded_data_{direction}_{timestamp}.npy"
                    np.save(filename, data_array)

                    metadata_filename = f"data/metadata_{direction}_{timestamp}.txt"
                    with open(metadata_filename, "w") as f:
                        f.write(f"Direction: {direction}\n")
                        f.write(f"Timestamp: {timestamp}\n")
                        f.write(f"Sample rate: {self.model.fs} Hz\n")
                        f.write(f"Channels: {self.model.n_ch}\n")
                        f.write(
                            f"Window length: {self.model.win_len / self.model.fs:.2f} seconds\n"
                        )
                        f.write(
                            f"Hop length: {self.model.hop / self.model.fs:.2f} seconds\n"
                        )
                        f.write(
                            f"Number of windows: {len(self.model.recorded_data[direction])}\n"
                        )
                        f.write(f"Data shape: {data_array.shape}\n")

            self.model.saving_success = True
            return True
        except Exception as e:
            self.model.saving_error = str(e)
            self.model.saving_success = False
            return False
