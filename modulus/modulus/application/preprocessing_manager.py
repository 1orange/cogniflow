"""Preprocessing pipeline management."""

from typing import Optional, Dict, Any
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline
from modulus.infrastructure.ml.gpu_utils import detect_gpu_stack, to_gpu_array


class PreprocessingManager:
    """Manages preprocessing pipeline construction and application."""

    def __init__(self, config: Dict[str, Any], use_gpu: bool = False, device_id: Optional[int] = None):
        """
        Initialize preprocessing manager with configuration.

        Args:
            config: Preprocessing configuration dictionary
        """
        self.config = config
        self.pipeline: Optional[Pipeline] = None
        self.use_gpu = use_gpu
        self.device_id = device_id
        self._gpu_state = detect_gpu_stack(device_id) if use_gpu else {"available": False}

        if self.use_gpu and not self._gpu_state.get("available"):
            fallback_reason = self._gpu_state.get("error") or "GPU stack not available"
            print(f"[Preprocessing] GPU requested but unavailable: {fallback_reason}. Using CPU preprocessing.")
            self.use_gpu = False

    def build(self, X: Optional[np.ndarray] = None) -> Pipeline:
        """
        Build preprocessing pipeline based on configuration.

        Args:
            X: Optional sample data for validation

        Returns:
            sklearn Pipeline object
        """
        steps = []

        # Add standard scaler if configured
        if self.config.get("standard_scaler", False):
            scaler_cls = self._gpu_scaler() if self.use_gpu else StandardScaler
            steps.append(("scaler", scaler_cls()))

        # Add PCA if configured
        pca_components = self.config.get("pca_components")
        if pca_components is not None:
            if isinstance(pca_components, int) and pca_components > 0:
                pca_cls = self._gpu_pca() if self.use_gpu else PCA
                steps.append(("pca", pca_cls(n_components=pca_components)))
            elif isinstance(pca_components, float) and 0 < pca_components < 1:
                pca_cls = self._gpu_pca() if self.use_gpu else PCA
                steps.append(("pca", pca_cls(n_components=pca_components)))

        # Create pipeline (empty pipeline is passthrough)
        if not steps:
            # Use a passthrough step
            from sklearn.preprocessing import FunctionTransformer

            steps.append(("passthrough", FunctionTransformer()))

        self.pipeline = Pipeline(steps)
        return self.pipeline

    def fit(self, X: np.ndarray) -> "PreprocessingManager":
        """
        Fit preprocessing pipeline on training data.

        Args:
            X: Training feature matrix

        Returns:
            Self for chaining
        """
        if self.pipeline is None:
            self.build()

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

        transformed = self.pipeline.transform(X)
        if self.use_gpu and self._gpu_state.get("available"):
            transformed, _ = to_gpu_array(transformed)
        return transformed

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        """
        Fit and transform in one step.

        Args:
            X: Feature matrix

        Returns:
            Transformed feature matrix
        """
        if self.pipeline is None:
            self.build()

        transformed = self.pipeline.fit_transform(X)
        if self.use_gpu and self._gpu_state.get("available"):
            transformed, _ = to_gpu_array(transformed)
        return transformed

    def _gpu_scaler(self):
        """Return cuML StandardScaler if available, otherwise sklearn."""
        try:
            return self._gpu_state["cuml"].preprocessing.StandardScaler
        except Exception:  # noqa: BLE001
            print("[Preprocessing] cuML StandardScaler not available; using CPU scaler.")
            self.use_gpu = False
            return StandardScaler

    def _gpu_pca(self):
        """Return cuML PCA if available, otherwise sklearn."""
        try:
            return self._gpu_state["cuml"].decomposition.PCA
        except Exception:  # noqa: BLE001
            print("[Preprocessing] cuML PCA not available; using CPU PCA.")
            self.use_gpu = False
            return PCA
