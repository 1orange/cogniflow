"""
Dummy data provider for testing without real EEG hardware.

Generates synthetic EEG-like signals with realistic characteristics
for development and testing purposes.
"""

import numpy as np
import threading
import time
from collections import deque
from typing import Optional


class DummyDataProvider:
    """
    Simulated EEG data provider for testing.
    
    Generates synthetic signals that mimic real EEG characteristics:
    - Alpha waves (8-12 Hz) - dominant when relaxed
    - Beta waves (12-30 Hz) - active thinking
    - Random noise
    - Occasional artifacts
    """
    
    def __init__(
        self,
        fs: int = 128,
        n_channels: int = 14,
        noise_level: float = 0.5,
        artifact_probability: float = 0.01,
    ):
        """
        Initialize the dummy provider.
        
        Args:
            fs: Sample rate in Hz
            n_channels: Number of channels to simulate
            noise_level: Amplitude of random noise (0-1)
            artifact_probability: Probability of artifact per sample
        """
        self.fs = fs
        self.n_channels = n_channels
        self.noise_level = noise_level
        self.artifact_probability = artifact_probability
        
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
        
        # Phase offsets for each channel (creates variation)
        self._phases = np.random.uniform(0, 2 * np.pi, n_channels)
        
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
        samples_per_batch = max(1, self.fs // 60)  # Generate ~60 batches/sec
        
        while self._running:
            current_time = time.time()
            elapsed = current_time - last_time
            
            # Calculate how many samples we should have generated
            expected_samples = int(elapsed * self.fs)
            
            if expected_samples >= samples_per_batch:
                samples = self._generate_samples(expected_samples)
                
                with self._lock:
                    for sample in samples:
                        self._buffer.append(sample)
                
                last_time = current_time
            else:
                time.sleep(1.0 / self.fs)  # Short sleep
                
    def _generate_samples(self, n_samples: int) -> np.ndarray:
        """
        Generate synthetic EEG samples.
        
        Args:
            n_samples: Number of samples to generate
            
        Returns:
            Array of shape (n_samples, n_channels)
        """
        t = np.arange(n_samples) / self.fs + self._sample_counter / self.fs
        self._sample_counter += n_samples
        
        samples = np.zeros((n_samples, self.n_channels))
        
        for ch in range(self.n_channels):
            phase = self._phases[ch]
            
            # Alpha waves (8-12 Hz) - microvolts scale
            alpha_freq = 10 + np.random.uniform(-1, 1)
            alpha = 20 * np.sin(2 * np.pi * alpha_freq * t + phase)
            
            # Beta waves (12-30 Hz)
            beta_freq = 20 + np.random.uniform(-2, 2)
            beta = 10 * np.sin(2 * np.pi * beta_freq * t + phase * 2)
            
            # Theta waves (4-8 Hz)
            theta_freq = 6 + np.random.uniform(-1, 1)
            theta = 15 * np.sin(2 * np.pi * theta_freq * t + phase * 0.5)
            
            # Random noise
            noise = self.noise_level * 30 * np.random.randn(n_samples)
            
            # Combine
            samples[:, ch] = alpha + beta + theta + noise
            
            # Occasional artifacts (large spikes)
            artifact_mask = np.random.random(n_samples) < self.artifact_probability
            samples[artifact_mask, ch] += np.random.choice([-1, 1]) * 150
            
        return samples
        
    def read(self, n_samples: int) -> np.ndarray:
        """
        Read samples from the buffer.
        
        Args:
            n_samples: Number of samples to read
            
        Returns:
            Array of shape (n_read, n_channels)
        """
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

