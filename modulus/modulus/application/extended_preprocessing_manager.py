"""
Extended Preprocessing Manager with custom preprocessing support.

This extends the base PreprocessingManager to support custom preprocessing
techniques while maintaining Clean Architecture principles.
"""

from typing import Optional, Dict, Any
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline

from modulus.application.custom_preprocessing import (
    TimeSeriesFeatureExtractor,
    ChannelSelector,
    MovingAverageFilter,
    RobustScaler,
    DimensionalityReducer,
    NotchFilter,
    BandPassFilter,
    SmoothingFilter,
    ArtifactRejection,
)


class ExtendedPreprocessingManager:
    """
    Extended preprocessing manager supporting custom preprocessing techniques.

    Supports the same config as PreprocessingManager, plus:
    - Time-series feature extraction
    - Channel selection
    - Moving average filtering
    - Robust scaling
    - Time-axis downsampling
    """

    def __init__(
        self,
        config: Dict[str, Any],
        n_timesteps: Optional[int] = None,
        n_channels: Optional[int] = None,
    ):
        """
        Initialize extended preprocessing manager.

        Args:
            config: Preprocessing configuration dictionary
            n_timesteps: Number of timesteps (for time-series preprocessing)
            n_channels: Number of channels (for time-series preprocessing)
        """
        self.config = config
        self.n_timesteps = n_timesteps
        self.n_channels = n_channels
        self.pipeline: Optional[Pipeline] = None

    def build(self, X: Optional[np.ndarray] = None) -> Pipeline:
        """
        Build preprocessing pipeline based on configuration.

        Args:
            X: Optional sample data for validation

        Returns:
            sklearn Pipeline object with custom preprocessing steps
        """
        steps = []

        # Infer dimensions from data if not provided
        if X is not None and self.n_timesteps is None and self.n_channels is None:
            # Try to infer if this is flattened time-series data
            # Common patterns: (n_samples, n_timesteps * n_channels)
            n_features = X.shape[1]
            # Try common combinations
            for nt in [192, 128, 256, 512]:
                if n_features % nt == 0:
                    self.n_timesteps = nt
                    self.n_channels = n_features // nt
                    print(
                        f"  Inferred dimensions: {nt} timesteps, {self.n_channels} channels"
                    )
                    break

        # Get sampling frequency
        fs = self.config.get("sampling_frequency", 128.0)

        # 1. EEG-specific preprocessing (if dimensions known)
        if self.n_timesteps and self.n_channels:
            # Notch filter - Remove 50/60 Hz power line noise
            if self.config.get("notch_filter", False):
                notch_freq = self.config.get("notch_freq", 50.0)
                notch_quality = self.config.get("notch_quality", 30.0)
                steps.append(
                    (
                        "notch_filter",
                        NotchFilter(
                            n_timesteps=self.n_timesteps,
                            n_channels=self.n_channels,
                            notch_freq=notch_freq,
                            fs=fs,
                            quality_factor=notch_quality,
                        ),
                    )
                )

            # Band-pass filter - Keep 0.5-40 Hz
            if self.config.get("bandpass_filter", False):
                lowcut = self.config.get("bandpass_low", 0.5)
                highcut = self.config.get("bandpass_high", 40.0)
                order = self.config.get("bandpass_order", 4)
                steps.append(
                    (
                        "bandpass_filter",
                        BandPassFilter(
                            n_timesteps=self.n_timesteps,
                            n_channels=self.n_channels,
                            lowcut=lowcut,
                            highcut=highcut,
                            fs=fs,
                            order=order,
                        ),
                    )
                )

            # Smoothing filter - Moving average with time window
            if self.config.get("smoothing_filter", False):
                window_ms = self.config.get("smoothing_window_ms", 100.0)
                steps.append(
                    (
                        "smoothing_filter",
                        SmoothingFilter(
                            n_timesteps=self.n_timesteps,
                            n_channels=self.n_channels,
                            window_ms=window_ms,
                            fs=fs,
                        ),
                    )
                )

            # Artifact rejection - Clean bad epochs
            if self.config.get("artifact_rejection", False):
                amplitude_threshold = self.config.get("amplitude_threshold", 100.0)
                flatline_threshold = self.config.get("flatline_threshold", 0.1)
                flatline_duration_ms = self.config.get("flatline_duration_ms", 200.0)
                hf_power_threshold = self.config.get("hf_power_threshold", 5.0)
                hf_freq_min = self.config.get("hf_freq_min", 30.0)
                reject_mode = self.config.get("reject_mode", "mark")
                steps.append(
                    (
                        "artifact_rejection",
                        ArtifactRejection(
                            n_timesteps=self.n_timesteps,
                            n_channels=self.n_channels,
                            amplitude_threshold=amplitude_threshold,
                            flatline_threshold=flatline_threshold,
                            flatline_duration_ms=flatline_duration_ms,
                            hf_power_threshold=hf_power_threshold,
                            hf_freq_min=hf_freq_min,
                            fs=fs,
                            reject_mode=reject_mode,
                        ),
                    )
                )

        # 2. Custom time-series preprocessing (if dimensions known)
        if self.n_timesteps and self.n_channels:
            # Downsampling (reduce dimensionality early)
            downsample_factor = self.config.get("downsample_factor")
            if downsample_factor and downsample_factor > 1:
                steps.append(
                    (
                        "downsample",
                        DimensionalityReducer(
                            n_timesteps=self.n_timesteps,
                            n_channels=self.n_channels,
                            downsample_factor=downsample_factor,
                        ),
                    )
                )
                # Update timesteps after downsampling
                self.n_timesteps = self.n_timesteps // downsample_factor

            # Moving average filter
            if self.config.get("moving_average", False):
                window_size = self.config.get("moving_average_window", 5)
                steps.append(
                    (
                        "smooth",
                        MovingAverageFilter(
                            n_timesteps=self.n_timesteps,
                            n_channels=self.n_channels,
                            window_size=window_size,
                        ),
                    )
                )

            # Channel selection
            selected_channels = self.config.get("selected_channels")
            if selected_channels:
                steps.append(
                    (
                        "channel_select",
                        ChannelSelector(
                            n_timesteps=self.n_timesteps,
                            n_channels=self.n_channels,
                            selected_channels=selected_channels,
                        ),
                    )
                )
                # Update number of channels
                self.n_channels = len(selected_channels)

            # Feature extraction
            if self.config.get("extract_features", False):
                feature_list = self.config.get(
                    "feature_list", ["mean", "std", "energy"]
                )
                steps.append(
                    (
                        "feature_extraction",
                        TimeSeriesFeatureExtractor(
                            n_timesteps=self.n_timesteps,
                            n_channels=self.n_channels,
                            features=feature_list,
                        ),
                    )
                )

        # 2. Standard scaling (with option for robust scaling)
        if self.config.get("robust_scaler", False):
            steps.append(("robust_scaler", RobustScaler()))
        elif self.config.get("standard_scaler", False):
            steps.append(("scaler", StandardScaler()))

        # 3. PCA (dimensionality reduction)
        pca_components = self.config.get("pca_components")
        if pca_components is not None:
            if isinstance(pca_components, int) and pca_components > 0:
                steps.append(("pca", PCA(n_components=pca_components)))
            elif isinstance(pca_components, float) and 0 < pca_components < 1:
                steps.append(("pca", PCA(n_components=pca_components)))

        # Create pipeline (empty pipeline is passthrough)
        if not steps:
            from sklearn.preprocessing import FunctionTransformer

            steps.append(("passthrough", FunctionTransformer()))

        self.pipeline = Pipeline(steps)
        return self.pipeline

    def fit(self, X: np.ndarray) -> "ExtendedPreprocessingManager":
        """
        Fit preprocessing pipeline on training data.

        Args:
            X: Training feature matrix

        Returns:
            Self for chaining
        """
        if self.pipeline is None:
            self.build(X)

        self.pipeline.fit(X)
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Transform data using fitted pipeline.

        Args:
            X: Feature matrix to transform

        Returns:
            Transformed feature matrix
        """
        if self.pipeline is None:
            raise RuntimeError(
                "Pipeline not built or fitted. Call build() or fit() first."
            )

        return self.pipeline.transform(X)

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        """
        Fit and transform in one step.

        Args:
            X: Feature matrix

        Returns:
            Transformed feature matrix
        """
        if self.pipeline is None:
            self.build(X)

        return self.pipeline.fit_transform(X)

    def get_feature_count(self) -> Optional[int]:
        """Get the number of output features after transformation."""
        if self.pipeline is None:
            return None

        # This would require a sample transform to determine
        return None


# Helper function to create extended preprocessing manager from config
def create_extended_preprocessing_manager(
    config: Dict[str, Any],
    n_timesteps: Optional[int] = None,
    n_channels: Optional[int] = None,
) -> ExtendedPreprocessingManager:
    """
    Factory function to create ExtendedPreprocessingManager.

    Args:
        config: Preprocessing configuration
        n_timesteps: Number of timesteps in time-series data
        n_channels: Number of channels in time-series data

    Returns:
        Configured ExtendedPreprocessingManager instance
    """
    return ExtendedPreprocessingManager(
        config=config,
        n_timesteps=n_timesteps,
        n_channels=n_channels,
    )
