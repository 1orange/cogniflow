"""
Data provider that wraps the Rust Emotiv reader for real-time streaming to the trainer.

Provides a buffered, non-blocking interface using the Rust reader (no Python thread).
"""

import numpy as np
import threading
from collections import deque
from typing import Optional

from emotiv_rs import EmotivReader as _RsReader
from bci.emotiv.constants import DEFAULT_VID, DEFAULT_PID, PACKET_SIZE_BYTES


class DataProvider:
    """
    Adapter that wraps bci.emotiv.EEGReader to provide a consistent,
    non-blocking interface for real-time applications.

    Converts EEGReader's blocking iterator into a buffered, thread-safe
    data source that can be polled for small chunks without blocking the UI.
    """

    def __init__(
        self,
        fs: int = 128,
        n_channels: int = 14,
        aes_key_hex: str | None = None,
        vid: int = DEFAULT_VID,
        pid: int = DEFAULT_PID,
    ):
        """
        Initialize the data provider.

        Args:
            fs: Expected sample rate (Hz). Emotiv EPOC runs at 128 Hz.
            n_channels: Number of EEG channels (14 for EPOC)
        """
        self.fs = fs
        self.n_channels = n_channels
        self.reader: Optional[_RsReader] = None
        self._running = False
        self._thread: Optional[threading.Thread] = (
            None  # kept for compatibility; unused
        )
        self._buffer = deque(maxlen=fs * 10)  # Buffer up to 10 seconds
        self._lock = threading.Lock()
        self._intended_label: Optional[str] = None
        self._aes_key_hex = aes_key_hex
        self._vid = vid
        self._pid = pid

        # Sensor names in order
        self.sensor_names = [
            "AF3",
            "F7",
            "F3",
            "FC5",
            "T7",
            "P7",
            "O1",
            "O2",
            "P8",
            "T8",
            "FC6",
            "F4",
            "F8",
            "AF4",
        ]

    def start(self):
        """Start reading from the Emotiv device (Rust backend)."""
        if self._running:
            return

        self._running = True
        self.reader = _RsReader(
            self._vid, self._pid, PACKET_SIZE_BYTES, self._aes_key_hex
        )
        self.reader.start()

    def stop(self):
        """Stop reading from the Emotiv device."""
        self._running = False
        if self.reader:
            self.reader.stop()
            self.reader = None

        with self._lock:
            self._buffer.clear()

    def read(self, n_samples: int) -> np.ndarray:
        """
        Read n_samples from the buffer (non-blocking).

        Args:
            n_samples: Number of samples to read

        Returns:
            numpy array of shape (n_samples, n_channels) in microvolts
        """
        # First, pull any new samples from the Rust reader (non-blocking)
        self._drain_channel()
        with self._lock:
            available = len(self._buffer)
            if available == 0:
                # Return zeros if no data available
                return np.zeros((n_samples, self.n_channels))

            # Take up to n_samples from the buffer
            to_take = min(n_samples, available)
            samples = [self._buffer.popleft() for _ in range(to_take)]

            # If we don't have enough samples, pad with zeros
            if to_take < n_samples:
                padding = np.zeros((n_samples - to_take, self.n_channels))
                samples = np.vstack([samples, padding])
            else:
                samples = np.array(samples)

            return samples

    def set_intended_label(self, label: Optional[str]):
        """
        Set the intended label for the current task.
        This is used for debugging/logging purposes.

        Args:
            label: The intended direction label or None
        """
        self._intended_label = label

    def _drain_channel(self):
        """Drain parsed packets from Rust channel into local buffer (non-blocking)."""
        if not self.reader:
            return
        while True:
            parsed = self.reader.poll_parsed()
            if parsed is None:
                break
            sensor_values = []
            for sensor_name in self.sensor_names:
                value = parsed["sensors"].get(sensor_name, 0)
                # Convert 14-bit value to microvolts (approximate scaling)
                uv_value = (value - 8192) * 0.51
                sensor_values.append(uv_value)
            sample = np.array(sensor_values)
            with self._lock:
                self._buffer.append(sample)
