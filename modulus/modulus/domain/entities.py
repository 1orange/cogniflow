"""Domain entities - Framework-agnostic data structures."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import numpy as np
import pandas as pd


@dataclass
class Dataset:
    """Represents a complete dataset with features, labels, and optional metadata."""

    X: np.ndarray
    y: np.ndarray
    metadata: Optional[pd.DataFrame] = None

    def __post_init__(self):
        """Validate dataset consistency."""
        if len(self.X) != len(self.y):
            raise ValueError(
                f"Feature and label dimensions mismatch: {len(self.X)} vs {len(self.y)}"
            )
        if self.metadata is not None and len(self.metadata) != len(self.X):
            raise ValueError(
                f"Metadata length mismatch: {len(self.metadata)} vs {len(self.X)}"
            )


@dataclass
class Splits:
    """Represents train/validation/test splits."""

    X_train: np.ndarray
    X_val: np.ndarray
    X_test: np.ndarray
    y_train: np.ndarray
    y_val: np.ndarray
    y_test: np.ndarray

    metadata_train: Optional[pd.DataFrame] = None
    metadata_val: Optional[pd.DataFrame] = None
    metadata_test: Optional[pd.DataFrame] = None


@dataclass
class SplitConfig:
    """Configuration for data splitting."""

    train: float
    val: float
    test: float
    random_state: int = 42
    stratify: bool = True

    def __post_init__(self):
        """Validate split ratios."""
        total = self.train + self.val + self.test
        if not (0.99 <= total <= 1.01):  # Allow small floating point errors
            raise ValueError(f"Split ratios must sum to 1.0, got {total}")
        if any(ratio <= 0 for ratio in [self.train, self.val, self.test]):
            raise ValueError("All split ratios must be positive")


@dataclass
class ModelSpec:
    """Specification for a machine learning model."""

    name: str
    params: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate model specification."""
        if not self.name:
            raise ValueError("Model name cannot be empty")


@dataclass
class MetricSet:
    """Collection of evaluation metrics for a model."""

    model_name: str
    metrics: Dict[str, float]
    split: str = "validation"  # or "test"

    def get_metric(self, name: str, default: float = 0.0) -> float:
        """Safely retrieve a metric value."""
        return self.metrics.get(name, default)

    def __repr__(self) -> str:
        metrics_str = ", ".join(f"{k}={v:.4f}" for k, v in self.metrics.items())
        return f"MetricSet({self.model_name}, {self.split}: {metrics_str})"


@dataclass
class PipelineConfig:
    """Complete pipeline configuration."""

    data_config: Dict[str, Any]
    preprocessing_config: Dict[str, Any]
    model_specs: list[ModelSpec]
    output_config: Dict[str, Any]

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "PipelineConfig":
        """Create PipelineConfig from dictionary."""
        model_specs = [
            ModelSpec(name=m["name"], params=m.get("params", {}))
            for m in config_dict.get("Models", [])
        ]

        return cls(
            data_config=config_dict.get("Data", {}),
            preprocessing_config=config_dict.get("Preprocessing", {}),
            model_specs=model_specs,
            output_config=config_dict.get("Output", {}),
        )
