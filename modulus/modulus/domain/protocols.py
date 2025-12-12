"""Protocol definitions (interfaces) for the domain layer."""

from typing import Protocol, Optional, Dict, Any, List
import numpy as np
import pandas as pd
from .entities import Dataset, Splits, SplitConfig, MetricSet


class IDataLoader(Protocol):
    """Interface for data loading."""

    def load(self) -> Dataset:
        """Load data and return Dataset entity."""
        ...


class IDataSplitter(Protocol):
    """Interface for data splitting."""

    def split(
        self,
        X: np.ndarray,
        y: np.ndarray,
        config: SplitConfig,
        metadata: Optional[pd.DataFrame] = None,
    ) -> Splits:
        """Split data into train/val/test sets."""
        ...


class IPreprocessor(Protocol):
    """Interface for preprocessing pipelines."""

    def fit(self, X: np.ndarray) -> "IPreprocessor":
        """Fit preprocessor on training data."""
        ...

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Transform data using fitted preprocessor."""
        ...

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        """Fit and transform in one step."""
        ...


class IModel(Protocol):
    """Interface for machine learning models."""

    def fit(self, X: np.ndarray, y: np.ndarray) -> "IModel":
        """Train the model."""
        ...

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions."""
        ...

    def predict_proba(self, X: np.ndarray) -> Optional[np.ndarray]:
        """Predict class probabilities (if applicable)."""
        ...


class IEvaluator(Protocol):
    """Interface for model evaluation."""

    def evaluate(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_proba: Optional[np.ndarray] = None,
    ) -> Dict[str, float]:
        """Evaluate predictions and return metrics."""
        ...


class IReportWriter(Protocol):
    """Interface for report writing."""

    def write(
        self,
        metrics: List[MetricSet],
        output_path: str,
        **kwargs: Any,
    ) -> None:
        """Write evaluation report to file."""
        ...


class IModelRegistry(Protocol):
    """Interface for model persistence."""

    def save(self, model: Any, name: str, path: str) -> None:
        """Save a trained model."""
        ...

    def load(self, name: str, path: str) -> Any:
        """Load a saved model."""
        ...
