"""
Custom preprocessing techniques that can be added to the PreprocessingManager.

This module demonstrates how to extend the modulus framework with custom
preprocessing steps following the Clean Architecture principles.
"""

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from scipy.signal import butter, filtfilt, iirnotch


class TimeSeriesFeatureExtractor(BaseEstimator, TransformerMixin):
    """
    Extract statistical features from flattened time-series data.

    Useful for EEG or sensor data that has been flattened from
    (n_samples, n_timesteps, n_channels) to (n_samples, n_timesteps * n_channels).
    """

    def __init__(self, n_timesteps: int, n_channels: int, features: list = None):
        """
        Initialize feature extractor.

        Args:
            n_timesteps: Number of timesteps in original data
            n_channels: Number of channels in original data
            features: List of features to extract. Options:
                - 'mean': Mean value per channel
                - 'std': Standard deviation per channel
                - 'min': Minimum value per channel
                - 'max': Maximum value per channel
                - 'range': Range (max-min) per channel
                - 'energy': Energy (sum of squares) per channel
        """
        self.n_timesteps = n_timesteps
        self.n_channels = n_channels
        self.features = features or ["mean", "std", "energy"]

    def fit(self, X, y=None):
        """Fit transformer (no-op for this transformer)."""
        return self

    def transform(self, X):
        """
        Extract statistical features from flattened time-series data.

        Args:
            X: Shape (n_samples, n_timesteps * n_channels)

        Returns:
            Features of shape (n_samples, n_features * n_channels)
        """
        n_samples = X.shape[0]

        # Reshape to 3D: (n_samples, n_timesteps, n_channels)
        X_reshaped = X.reshape(n_samples, self.n_timesteps, self.n_channels)

        extracted_features = []

        for feature_name in self.features:
            if feature_name == "mean":
                feat = np.mean(X_reshaped, axis=1)  # (n_samples, n_channels)
            elif feature_name == "std":
                feat = np.std(X_reshaped, axis=1)
            elif feature_name == "min":
                feat = np.min(X_reshaped, axis=1)
            elif feature_name == "max":
                feat = np.max(X_reshaped, axis=1)
            elif feature_name == "range":
                feat = np.ptp(X_reshaped, axis=1)  # peak-to-peak (range)
            elif feature_name == "energy":
                feat = np.sum(X_reshaped**2, axis=1)
            elif feature_name == "variance":
                feat = np.var(X_reshaped, axis=1)
            else:
                raise ValueError(f"Unknown feature: {feature_name}")

            extracted_features.append(feat)

        # Concatenate all features: (n_samples, n_features * n_channels)
        result = np.hstack(extracted_features)

        return result


class ChannelSelector(BaseEstimator, TransformerMixin):
    """
    Select specific channels from flattened time-series data.

    Useful for focusing on specific EEG channels or sensor positions.
    """

    def __init__(self, n_timesteps: int, n_channels: int, selected_channels: list):
        """
        Initialize channel selector.

        Args:
            n_timesteps: Number of timesteps in original data
            n_channels: Number of channels in original data
            selected_channels: List of channel indices to keep (0-indexed)
        """
        self.n_timesteps = n_timesteps
        self.n_channels = n_channels
        self.selected_channels = selected_channels

    def fit(self, X, y=None):
        """Fit transformer (no-op for this transformer)."""
        return self

    def transform(self, X):
        """
        Select specific channels from flattened data.

        Args:
            X: Shape (n_samples, n_timesteps * n_channels)

        Returns:
            Data with shape (n_samples, n_timesteps * len(selected_channels))
        """
        n_samples = X.shape[0]

        # Reshape to 3D
        X_reshaped = X.reshape(n_samples, self.n_timesteps, self.n_channels)

        # Select channels
        X_selected = X_reshaped[:, :, self.selected_channels]

        # Flatten back
        return X_selected.reshape(n_samples, -1)


class MovingAverageFilter(BaseEstimator, TransformerMixin):
    """
    Apply moving average filter to smooth time-series data.

    Helps reduce noise in EEG or sensor signals.
    """

    def __init__(self, n_timesteps: int, n_channels: int, window_size: int = 5):
        """
        Initialize moving average filter.

        Args:
            n_timesteps: Number of timesteps in original data
            n_channels: Number of channels in original data
            window_size: Size of moving average window
        """
        self.n_timesteps = n_timesteps
        self.n_channels = n_channels
        self.window_size = window_size

    def fit(self, X, y=None):
        """Fit transformer (no-op for this transformer)."""
        return self

    def transform(self, X):
        """
        Apply moving average filter.

        Args:
            X: Shape (n_samples, n_timesteps * n_channels)

        Returns:
            Smoothed data with same shape
        """
        n_samples = X.shape[0]

        # Reshape to 3D
        X_reshaped = X.reshape(n_samples, self.n_timesteps, self.n_channels)

        # Apply moving average along time axis
        kernel = np.ones(self.window_size) / self.window_size
        X_smoothed = np.zeros_like(X_reshaped)

        for i in range(n_samples):
            for j in range(self.n_channels):
                X_smoothed[i, :, j] = np.convolve(
                    X_reshaped[i, :, j], kernel, mode="same"
                )

        # Flatten back
        return X_smoothed.reshape(n_samples, -1)


class RobustScaler(BaseEstimator, TransformerMixin):
    """
    Robust scaler using median and IQR instead of mean and std.

    More robust to outliers than StandardScaler.
    """

    def __init__(self):
        """Initialize robust scaler."""
        self.median_ = None
        self.iqr_ = None

    def fit(self, X, y=None):
        """
        Compute median and IQR from training data.

        Args:
            X: Training data
            y: Ignored

        Returns:
            Self for chaining
        """
        self.median_ = np.median(X, axis=0)
        q75 = np.percentile(X, 75, axis=0)
        q25 = np.percentile(X, 25, axis=0)
        self.iqr_ = q75 - q25

        # Avoid division by zero
        self.iqr_[self.iqr_ == 0] = 1.0

        return self

    def transform(self, X):
        """
        Scale data using median and IQR.

        Args:
            X: Data to transform

        Returns:
            Scaled data
        """
        if self.median_ is None or self.iqr_ is None:
            raise RuntimeError("Scaler not fitted. Call fit() first.")

        return (X - self.median_) / self.iqr_


class DimensionalityReducer(BaseEstimator, TransformerMixin):
    """
    Reduce dimensionality by downsampling time axis.

    Useful for very high-dimensional time-series data.
    """

    def __init__(self, n_timesteps: int, n_channels: int, downsample_factor: int = 2):
        """
        Initialize dimensionality reducer.

        Args:
            n_timesteps: Number of timesteps in original data
            n_channels: Number of channels in original data
            downsample_factor: Factor by which to reduce timesteps (e.g., 2 = half)
        """
        self.n_timesteps = n_timesteps
        self.n_channels = n_channels
        self.downsample_factor = downsample_factor

    def fit(self, X, y=None):
        """Fit transformer (no-op for this transformer)."""
        return self

    def transform(self, X):
        """
        Downsample time axis.

        Args:
            X: Shape (n_samples, n_timesteps * n_channels)

        Returns:
            Downsampled data
        """
        n_samples = X.shape[0]

        # Reshape to 3D
        X_reshaped = X.reshape(n_samples, self.n_timesteps, self.n_channels)

        # Downsample time axis
        X_downsampled = X_reshaped[:, :: self.downsample_factor, :]

        # Flatten back
        return X_downsampled.reshape(n_samples, -1)


class NotchFilter(BaseEstimator, TransformerMixin):
    """
    Apply notch filter to remove power line noise (50 Hz or 60 Hz).

    Essential for EEG data to remove electrical interference.
    """

    def __init__(
        self,
        n_timesteps: int,
        n_channels: int,
        notch_freq: float = 50.0,
        fs: float = 128.0,
        quality_factor: float = 30.0,
    ):
        """
        Initialize notch filter.

        Args:
            n_timesteps: Number of timesteps in data
            n_channels: Number of channels in data
            notch_freq: Frequency to remove (Hz), typically 50 Hz (EU) or 60 Hz (US)
            fs: Sampling frequency (Hz)
            quality_factor: Quality factor (higher = narrower notch)
        """
        self.n_timesteps = n_timesteps
        self.n_channels = n_channels
        self.notch_freq = notch_freq
        self.fs = fs
        self.quality_factor = quality_factor

        # Design the notch filter
        self.b, self.a = iirnotch(notch_freq, quality_factor, fs)

    def fit(self, X, y=None):
        """Fit transformer (no-op for this filter)."""
        return self

    def transform(self, X):
        """
        Apply notch filter to remove power line noise.

        Args:
            X: Flattened data, shape (n_samples, n_timesteps * n_channels)

        Returns:
            Filtered data with same shape
        """
        n_samples = X.shape[0]

        # Reshape to 3D: (n_samples, n_timesteps, n_channels)
        X_reshaped = X.reshape(n_samples, self.n_timesteps, self.n_channels)

        # Apply notch filter to each sample and channel
        X_filtered = np.zeros_like(X_reshaped)

        for i in range(n_samples):
            for j in range(self.n_channels):
                X_filtered[i, :, j] = filtfilt(self.b, self.a, X_reshaped[i, :, j])

        # Flatten back to 2D
        return X_filtered.reshape(n_samples, -1)


class BandPassFilter(BaseEstimator, TransformerMixin):
    """
    Apply band-pass filter to retain specific frequency range.

    Typical EEG preprocessing: 0.5-40 Hz to remove DC drift and high-frequency noise.
    """

    def __init__(
        self,
        n_timesteps: int,
        n_channels: int,
        lowcut: float = 0.5,
        highcut: float = 40.0,
        fs: float = 128.0,
        order: int = 4,
    ):
        """
        Initialize band-pass filter.

        Args:
            n_timesteps: Number of timesteps in data
            n_channels: Number of channels in data
            lowcut: Low frequency cutoff (Hz)
            highcut: High frequency cutoff (Hz)
            fs: Sampling frequency (Hz)
            order: Filter order
        """
        self.n_timesteps = n_timesteps
        self.n_channels = n_channels
        self.lowcut = lowcut
        self.highcut = highcut
        self.fs = fs
        self.order = order

        # Design the band-pass filter
        nyquist = 0.5 * fs
        low = lowcut / nyquist
        high = highcut / nyquist
        self.b, self.a = butter(order, [low, high], btype="band")

    def fit(self, X, y=None):
        """Fit transformer (no-op for this filter)."""
        return self

    def transform(self, X):
        """
        Apply band-pass filter.

        Args:
            X: Flattened data, shape (n_samples, n_timesteps * n_channels)

        Returns:
            Filtered data with same shape
        """
        n_samples = X.shape[0]

        # Reshape to 3D
        X_reshaped = X.reshape(n_samples, self.n_timesteps, self.n_channels)

        # Apply filter to each sample and channel
        X_filtered = np.zeros_like(X_reshaped)

        for i in range(n_samples):
            for j in range(self.n_channels):
                X_filtered[i, :, j] = filtfilt(self.b, self.a, X_reshaped[i, :, j])

        # Flatten back
        return X_filtered.reshape(n_samples, -1)


class SmoothingFilter(BaseEstimator, TransformerMixin):
    """
    Apply moving average for smoothing based on time window (e.g., 100 ms).

    Reduces high-frequency noise while preserving signal characteristics.
    """

    def __init__(
        self,
        n_timesteps: int,
        n_channels: int,
        window_ms: float = 100.0,
        fs: float = 128.0,
    ):
        """
        Initialize smoothing filter.

        Args:
            n_timesteps: Number of timesteps in data
            n_channels: Number of channels in data
            window_ms: Window size in milliseconds
            fs: Sampling frequency (Hz)
        """
        self.n_timesteps = n_timesteps
        self.n_channels = n_channels
        self.window_ms = window_ms
        self.fs = fs

        # Convert window from ms to samples
        self.window_samples = int((window_ms / 1000.0) * fs)
        if self.window_samples < 1:
            self.window_samples = 1

    def fit(self, X, y=None):
        """Fit transformer (no-op for this filter)."""
        return self

    def transform(self, X):
        """
        Apply moving average smoothing.

        Args:
            X: Flattened data, shape (n_samples, n_timesteps * n_channels)

        Returns:
            Smoothed data with same shape
        """
        n_samples = X.shape[0]

        # Reshape to 3D
        X_reshaped = X.reshape(n_samples, self.n_timesteps, self.n_channels)

        # Create moving average kernel
        kernel = np.ones(self.window_samples) / self.window_samples

        # Apply smoothing
        X_smoothed = np.zeros_like(X_reshaped)

        for i in range(n_samples):
            for j in range(self.n_channels):
                X_smoothed[i, :, j] = np.convolve(
                    X_reshaped[i, :, j], kernel, mode="same"
                )

        # Flatten back
        return X_smoothed.reshape(n_samples, -1)


class ArtifactRejection(BaseEstimator, TransformerMixin):
    """
    Automatic artifact removal using epoch rejection with thresholds.

    Removes epochs with:
    - Excessive amplitude (> threshold µV)
    - Flatline / dead channels
    - High-frequency noise
    """

    def __init__(
        self,
        n_timesteps: int,
        n_channels: int,
        amplitude_threshold: float = 100.0,  # µV
        flatline_threshold: float = 0.1,  # µV (essentially zero)
        flatline_duration_ms: float = 200.0,  # ms
        hf_power_threshold: float = 5.0,  # Relative power threshold
        hf_freq_min: float = 30.0,  # Hz
        fs: float = 128.0,
        reject_mode: str = "mark",  # 'mark' or 'interpolate'
    ):
        """
        Initialize artifact rejection.

        Args:
            n_timesteps: Number of timesteps in data
            n_channels: Number of channels in data
            amplitude_threshold: Peak-to-peak amplitude threshold (µV)
            flatline_threshold: Threshold for detecting flat channels (µV)
            flatline_duration_ms: Duration of flatline to trigger rejection (ms)
            hf_power_threshold: Relative power threshold for high-frequency noise
            hf_freq_min: Minimum frequency for high-frequency noise detection (Hz)
            fs: Sampling frequency (Hz)
            reject_mode: 'mark' (mark bad epochs) or 'interpolate' (interpolate)
        """
        self.n_timesteps = n_timesteps
        self.n_channels = n_channels
        self.amplitude_threshold = amplitude_threshold
        self.flatline_threshold = flatline_threshold
        self.flatline_duration_ms = flatline_duration_ms
        self.hf_power_threshold = hf_power_threshold
        self.hf_freq_min = hf_freq_min
        self.fs = fs
        self.reject_mode = reject_mode

        # Convert flatline duration to samples
        self.flatline_samples = int((flatline_duration_ms / 1000.0) * fs)

        # Statistics for reporting
        self.n_rejected_amplitude = 0
        self.n_rejected_flatline = 0
        self.n_rejected_hf_noise = 0

    def fit(self, X, y=None):
        """Fit transformer (just resets statistics)."""
        self.n_rejected_amplitude = 0
        self.n_rejected_flatline = 0
        self.n_rejected_hf_noise = 0
        return self

    def _check_amplitude(self, epoch):
        """Check if epoch exceeds amplitude threshold."""
        peak_to_peak = np.ptp(epoch, axis=0)  # Per channel
        return np.any(peak_to_peak > self.amplitude_threshold)

    def _check_flatline(self, epoch):
        """Check if any channel is flat for too long."""
        for ch in range(epoch.shape[1]):
            signal = epoch[:, ch]

            # Find consecutive samples below flatline threshold
            flat_mask = np.abs(signal - np.mean(signal)) < self.flatline_threshold

            # Count consecutive True values
            consecutive_count = 0
            max_consecutive = 0

            for is_flat in flat_mask:
                if is_flat:
                    consecutive_count += 1
                    max_consecutive = max(max_consecutive, consecutive_count)
                else:
                    consecutive_count = 0

            if max_consecutive >= self.flatline_samples:
                return True

        return False

    def _check_hf_noise(self, epoch):
        """Check for excessive high-frequency noise."""
        for ch in range(epoch.shape[1]):
            signal = epoch[:, ch]

            # Compute power spectrum (simple approach)
            fft = np.fft.rfft(signal)
            power = np.abs(fft) ** 2
            freqs = np.fft.rfftfreq(len(signal), 1.0 / self.fs)

            # High-frequency range
            hf_mask = freqs >= self.hf_freq_min

            if np.any(hf_mask):
                hf_power = np.mean(power[hf_mask])
                total_power = np.mean(power)

                if total_power > 0:
                    relative_hf_power = hf_power / total_power

                    if relative_hf_power > self.hf_power_threshold:
                        return True

        return False

    def transform(self, X):
        """
        Apply artifact rejection.

        Args:
            X: Flattened data, shape (n_samples, n_timesteps * n_channels)

        Returns:
            Cleaned data (marked or interpolated)
        """
        n_samples = X.shape[0]

        # Reshape to 3D
        X_reshaped = X.reshape(n_samples, self.n_timesteps, self.n_channels)

        # Create output array
        X_cleaned = X_reshaped.copy()

        # Track bad epochs
        bad_epochs = []

        for i in range(n_samples):
            epoch = X_reshaped[i]

            is_bad = False

            # Check amplitude
            if self._check_amplitude(epoch):
                self.n_rejected_amplitude += 1
                is_bad = True

            # Check flatline
            if self._check_flatline(epoch):
                self.n_rejected_flatline += 1
                is_bad = True

            # Check high-frequency noise
            if self._check_hf_noise(epoch):
                self.n_rejected_hf_noise += 1
                is_bad = True

            if is_bad:
                bad_epochs.append(i)

                if self.reject_mode == "mark":
                    # Mark as zero (or NaN)
                    X_cleaned[i] = 0.0
                elif self.reject_mode == "interpolate":
                    # Simple interpolation: use mean of neighboring good epochs
                    # Find nearest good epochs
                    prev_good = i - 1
                    next_good = i + 1

                    while prev_good >= 0 and prev_good in bad_epochs:
                        prev_good -= 1

                    while next_good < n_samples and next_good in bad_epochs:
                        next_good += 1

                    if prev_good >= 0 and next_good < n_samples:
                        # Average of neighbors
                        X_cleaned[i] = (
                            X_reshaped[prev_good] + X_reshaped[next_good]
                        ) / 2.0
                    elif prev_good >= 0:
                        X_cleaned[i] = X_reshaped[prev_good]
                    elif next_good < n_samples:
                        X_cleaned[i] = X_reshaped[next_good]

        # Store rejection statistics
        self.bad_epochs_ = bad_epochs
        self.rejection_rate_ = len(bad_epochs) / n_samples if n_samples > 0 else 0

        # Flatten back
        return X_cleaned.reshape(n_samples, -1)

    def get_rejection_stats(self):
        """Get artifact rejection statistics."""
        return {
            "n_rejected_amplitude": self.n_rejected_amplitude,
            "n_rejected_flatline": self.n_rejected_flatline,
            "n_rejected_hf_noise": self.n_rejected_hf_noise,
            "total_bad_epochs": len(self.bad_epochs_)
            if hasattr(self, "bad_epochs_")
            else 0,
            "rejection_rate": self.rejection_rate_
            if hasattr(self, "rejection_rate_")
            else 0,
        }


# Example: How to use custom preprocessing in your pipeline
def example_usage():
    """
    Example of how to use custom preprocessing techniques.

    This demonstrates how to extend the PreprocessingManager with
    custom preprocessing steps.
    """
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA

    # Define your data dimensions
    N_TIMESTEPS = 192
    N_CHANNELS = 14

    # Create a custom preprocessing pipeline (EEG-specific)
    custom_pipeline = Pipeline(
        [
            # 1. Remove power line noise (50 Hz in EU, 60 Hz in US)
            (
                "notch",
                NotchFilter(
                    n_timesteps=N_TIMESTEPS,
                    n_channels=N_CHANNELS,
                    notch_freq=50.0,  # 50 Hz for EU
                    fs=128.0,
                ),
            ),
            # 2. Band-pass filter (0.5-40 Hz) - standard EEG preprocessing
            (
                "bandpass",
                BandPassFilter(
                    n_timesteps=N_TIMESTEPS,
                    n_channels=N_CHANNELS,
                    lowcut=0.5,
                    highcut=40.0,
                    fs=128.0,
                ),
            ),
            # 3. Smooth with 100ms moving average
            (
                "smooth",
                SmoothingFilter(
                    n_timesteps=N_TIMESTEPS,
                    n_channels=N_CHANNELS,
                    window_ms=100.0,
                    fs=128.0,
                ),
            ),
            # 4. Artifact rejection
            (
                "artifact_reject",
                ArtifactRejection(
                    n_timesteps=N_TIMESTEPS,
                    n_channels=N_CHANNELS,
                    amplitude_threshold=100.0,  # 100 µV
                    flatline_duration_ms=200.0,
                    hf_power_threshold=5.0,
                    fs=128.0,
                    reject_mode="mark",  # or 'interpolate'
                ),
            ),
            # 2. Optional: Select specific channels
            # ('channel_select', ChannelSelector(
            #     n_timesteps=N_TIMESTEPS,
            #     n_channels=N_CHANNELS,
            #     selected_channels=[0, 1, 2, 3, 4]  # Keep first 5 channels
            # )),
            # 3. Extract statistical features
            (
                "features",
                TimeSeriesFeatureExtractor(
                    n_timesteps=N_TIMESTEPS,
                    n_channels=N_CHANNELS,
                    features=["mean", "std", "energy", "range"],
                ),
            ),
            # 4. Scale features
            ("scaler", StandardScaler()),
            # 5. Optional: Dimensionality reduction
            ("pca", PCA(n_components=50)),
        ]
    )

    return custom_pipeline


if __name__ == "__main__":
    print("Custom Preprocessing Module for Modulus Framework")
    print("=" * 60)
    print("\nAvailable custom transformers:")
    print("\nGeneral Preprocessing:")
    print("  1. TimeSeriesFeatureExtractor - Extract statistical features")
    print("  2. ChannelSelector - Select specific channels")
    print("  3. MovingAverageFilter - Smooth signals")
    print("  4. RobustScaler - Robust scaling with median/IQR")
    print("  5. DimensionalityReducer - Downsample time axis")
    print("\nEEG-Specific Preprocessing:")
    print("  6. NotchFilter - Remove 50/60 Hz power line noise")
    print("  7. BandPassFilter - Keep 0.5-40 Hz range (standard EEG)")
    print("  8. SmoothingFilter - Moving average with time window (ms)")
    print("  9. ArtifactRejection - Automatic epoch rejection")
    print("\nSee example_usage() for integration examples.")
