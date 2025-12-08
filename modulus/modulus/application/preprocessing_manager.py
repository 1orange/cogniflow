"""Preprocessing pipeline management."""

from typing import Optional, Dict, Any
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline


class PreprocessingManager:
    """Manages preprocessing pipeline construction and application."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize preprocessing manager with configuration.

        Args:
            config: Preprocessing configuration dictionary
        """
        self.config = config
        self.pipeline: Optional[Pipeline] = None

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
            steps.append(("scaler", StandardScaler()))

        # Add PCA if configured
        pca_components = self.config.get("pca_components")
        if pca_components is not None:
            if isinstance(pca_components, int) and pca_components > 0:
                steps.append(("pca", PCA(n_components=pca_components)))
            elif isinstance(pca_components, float) and 0 < pca_components < 1:
                steps.append(("pca", PCA(n_components=pca_components)))

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
            self.build()

        return self.pipeline.fit_transform(X)
