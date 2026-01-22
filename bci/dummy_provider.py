"""
Dummy data provider for testing without real EEG hardware.

Generates random EEG-like signals for development and testing purposes.
"""

import numpy as np
import threading
import time
from collections import deque
from typing import Optional


class DummyDataProvider:
    """
    Simulated EEG data provider for testing.
    
    Generates random signals with EEG-like characteristics.
    """
    
    def __init__(
        self,
        fs: int = 128,
        n_channels: int = 14,
        noise_level: float = 1.0,
    ):
        """
        Initialize the dummy provider.
        
        Args:
            fs: Sample rate in Hz
            n_channels: Number of channels to simulate
            noise_level: Amplitude multiplier for signals
        """
        self.fs = fs
        self.n_channels = n_channels
        self.noise_level = noise_level
        
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._buffer = deque(maxlen=fs * 10)
        self._lock = threading.Lock()
        self._sample_counter = 0
        self._intended_label: Optional[str] = None
        
        # Sensor names (same as Emotiv EPOC)
        self.sensor_names = [
            "AF3", "F7", "F3", "FC5", "T7", "P7", "O1",
            "O2", "P8", "T8", "FC6", "F4", "F8", "AF4",
        ]
        
    def start(self):
        """Start generating synthetic data."""
        if self._running:
            return
            
        self._running = True
        self._thread = threading.Thread(target=self._generate_loop, daemon=True)
        self._thread.start()
        
    def stop(self):
        """Stop data generation."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None
            
    def _generate_loop(self):
        """Background thread that generates samples at the correct rate."""
        last_time = time.time()
        samples_per_batch = max(1, self.fs // 60)
        
        while self._running:
            current_time = time.time()
            elapsed = current_time - last_time
            expected_samples = int(elapsed * self.fs)
            
            if expected_samples >= samples_per_batch:
                samples = self._generate_samples(expected_samples)
                
                with self._lock:
                    for sample in samples:
                        self._buffer.append(sample)
                
                last_time = current_time
            else:
                time.sleep(1.0 / self.fs)
                
    def _generate_samples(self, n_samples: int) -> np.ndarray:
        """Generate random EEG-like samples."""
        # Random values in typical EEG microvolt range (-100 to 100 uV)
        samples = self.noise_level * 50 * np.random.randn(n_samples, self.n_channels)
        return samples
        
    def read(self, n_samples: int) -> np.ndarray:
        """Read samples from the buffer."""
        with self._lock:
            available = len(self._buffer)
            n_read = min(n_samples, available)
            
            if n_read == 0:
                return np.zeros((0, self.n_channels))
            
            samples = []
            for _ in range(n_read):
                samples.append(self._buffer.popleft())
                
            return np.array(samples)
            
    def set_intended_label(self, label: Optional[str]):
        """Set intended label (for compatibility)."""
        self._intended_label = label
        
    def clear_intended_label(self):
        """Clear intended label."""
        self._intended_label = None
        
    @property
    def is_running(self) -> bool:
        """Check if provider is running."""
        return self._running
