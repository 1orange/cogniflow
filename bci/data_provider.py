"""
Data provider that wraps EEGReader for real-time streaming to the trainer.

Provides a buffered, non-blocking interface with background threading and
proper data format conversion for the trainer application.
"""

import numpy as np
import threading
import time
from collections import deque
from typing import Optional

from bci.emotiv import EEGReader


class DataProvider:
    """
    Adapter that wraps bci.emotiv.EEGReader to provide a consistent,
    non-blocking interface for real-time applications.
    
    Converts EEGReader's blocking iterator into a buffered, thread-safe
    data source that can be polled for small chunks without blocking the UI.
    """
    
    def __init__(self, fs: int = 128, n_channels: int = 14):
        """
        Initialize the data provider.
        
        Args:
            fs: Expected sample rate (Hz). Emotiv EPOC runs at 128 Hz.
            n_channels: Number of EEG channels (14 for EPOC)
        """
        self.fs = fs
        self.n_channels = n_channels
        self.reader: Optional[EEGReader] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._buffer = deque(maxlen=fs * 10)  # Buffer up to 10 seconds
        self._lock = threading.Lock()
        self._intended_label: Optional[str] = None
        
        # Sensor names in order
        self.sensor_names = [
            "AF3", "F7", "F3", "FC5", "T7", "P7", "O1",
            "O2", "P8", "T8", "FC6", "F4", "F8", "AF4"
        ]
    
    def start(self):
        """Start reading from the Emotiv device."""
        if self._running:
            return
        
        self._running = True
        self.reader = EEGReader()
        self.reader.open()
        
        # Start background thread to read data
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()
        
        # Give it a moment to start collecting data
        time.sleep(0.1)
    
    def stop(self):
        """Stop reading from the Emotiv device."""
        self._running = False
        
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        
        if self.reader:
            self.reader.close()
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
    
    def _read_loop(self):
        """Background thread that continuously reads from the Emotiv device."""
        try:
            for packet in self.reader.read_parsed():
                if not self._running:
                    break
                
                # Convert sensor data to numpy array
                sensor_values = []
                for sensor_name in self.sensor_names:
                    value = packet.sensors.get(sensor_name, 0)
                    # Convert 14-bit value to microvolts (approximate scaling)
                    # EPOC reports 14-bit values (0-16383), scale to ±4096 µV range
                    uv_value = (value - 8192) * 0.51
                    sensor_values.append(uv_value)
                
                sample = np.array(sensor_values)
                
                with self._lock:
                    self._buffer.append(sample)
        
        except Exception as e:
            print(f"Error in data provider read loop: {e}")
            self._running = False

