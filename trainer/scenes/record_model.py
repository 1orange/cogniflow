"""Model for RecordScene - holds state and data."""

import numpy as np
import random
from config import SAMPLE_RATE, N_CHANNELS, WIN_SEC, HOP_SEC, TASK_SEC, TRIALS_PER_CLASS
from bci.utils import LABELS


class RecordModel:
    """Model for RecordScene - stores state and data without rendering logic."""

    def __init__(self):
        self.fs = SAMPLE_RATE
        self.n_ch = N_CHANNELS
        self.win_len = int(WIN_SEC * self.fs)
        self.hop = int(HOP_SEC * self.fs)
        self.chan_buf = np.zeros((0, self.n_ch))

        # Wizard state
        self.wizard_step = "select_directions"  # 'select_directions', 'select_window', 'select_trials', 'recording', 'saving', 'complete'
        self.selected_directions = {label: True for label in LABELS}
        self.window_duration = TASK_SEC
        self.trials_per_direction = TRIALS_PER_CLASS

        # Recording state
        self.order = []
        self.trial_idx = 0
        self.intended = None
        self.phase = "baseline"  # 'baseline', 'task', 'rest'
        self.phase_start_time = None
        self.recorded_data = {}

        # Saving state
        self.saving_complete = False
        self.saving_success = False
        self.saving_error = None

    def get_selected_directions_list(self):
        """Get list of selected directions."""
        return [
            label
            for label, is_selected in self.selected_directions.items()
            if is_selected
        ]

    def toggle_direction(self, index):
        """Toggle direction selection."""
        if 0 <= index < len(LABELS):
            label = LABELS[index]
            self.selected_directions[label] = not self.selected_directions[label]

    def initialize_recording(self):
        """Initialize recording with selected parameters."""
        selected = self.get_selected_directions_list()
        self.recorded_data = {lab: [] for lab in selected}
        self.order = []
        [self.order.extend([lab] * self.trials_per_direction) for lab in selected]
        random.shuffle(self.order)
        self.trial_idx = 0
        self.intended = self.order[0] if self.order else None
        self.phase = "baseline"

    def get_current_trial_info(self):
        """Get information about current trial."""
        return {
            "trial_num": self.trial_idx + 1,
            "total_trials": len(self.order),
            "intended": self.intended,
            "phase": self.phase,
        }

    def advance_phase(self):
        """Advance to next phase or trial."""
        if self.phase == "baseline":
            self.phase = "task"
        elif self.phase == "task":
            self.phase = "rest"
        else:  # rest
            self.trial_idx += 1
            if self.trial_idx >= len(self.order):
                return False  # All trials complete
            self.intended = self.order[self.trial_idx]
            self.phase = "baseline"
        return True

    def add_samples(self, samples):
        """Add samples to channel buffer."""
        if samples.shape[1] != self.n_ch:
            samples = np.pad(
                samples, ((0, 0), (0, max(0, self.n_ch - samples.shape[1])))
            )[:, : self.n_ch]
        self.chan_buf = np.vstack([self.chan_buf, samples])
        if self.chan_buf.shape[0] > self.win_len * 3:
            self.chan_buf = self.chan_buf[-self.win_len * 2 :, :]

    def extract_windows(self):
        """Extract windows from buffer during task phase."""
        extracted = []
        while self.chan_buf.shape[0] >= self.win_len:
            win = self.chan_buf[: self.win_len, :]
            self.chan_buf = self.chan_buf[self.hop :, :]
            extracted.append(win.copy())
        return extracted
