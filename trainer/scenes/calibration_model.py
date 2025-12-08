"""Model for CalibrationScene - holds state and data."""

import numpy as np
import random
from config import SAMPLE_RATE, N_CHANNELS, WIN_SEC, HOP_SEC, TRIALS_PER_CLASS
from bci.utils import LABELS


class CalibrationModel:
    """Model for CalibrationScene - stores state and data without rendering logic."""

    def __init__(self):
        self.fs = SAMPLE_RATE
        self.n_ch = N_CHANNELS
        self.win_len = int(WIN_SEC * self.fs)
        self.hop = int(HOP_SEC * self.fs)
        self.chan_buf = np.zeros((0, self.n_ch))
        self.windows = {lab: [] for lab in LABELS}

        # Trial management
        order = []
        [order.extend([lab] * TRIALS_PER_CLASS) for lab in LABELS]
        random.shuffle(order)
        self.order = order
        self.trial_idx = 0
        self.intended = self.order[0] if self.order else None

        # Phase management
        self.phase = "baseline"  # 'baseline', 'task', 'rest'
        self.phase_start_time = None

        # Training
        self.training_complete = False
        self.balanced_accuracy = None
        self.training_error = None

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

    def set_phase_start_time(self, time_value):
        """Set phase start time."""
        self.phase_start_time = time_value

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

    def set_training_result(self, balanced_accuracy):
        """Set training result."""
        self.training_complete = True
        self.balanced_accuracy = balanced_accuracy

    def set_training_error(self, error):
        """Set training error."""
        self.training_complete = True
        self.training_error = error
