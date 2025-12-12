"""Scikit-learn model and evaluation adapters."""

from typing import Optional, Dict, Any
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    mean_squared_error,
    mean_absolute_error,
    r2_score,
)
from modulus.infrastructure.ml.gpu_utils import ensure_numpy


class SklearnModelAdapter:
    """Adapter for scikit-learn models to match IModel protocol."""

    def __init__(self, model: Any):
        """
        Initialize with a scikit-learn model instance.

        Args:
            model: Scikit-learn model (e.g., LogisticRegression, RandomForest)
        """
        self.model = model

    def fit(self, X: np.ndarray, y: np.ndarray) -> "SklearnModelAdapter":
        """Train the model."""
        self.model.fit(X, y)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions."""
        return self.model.predict(X)

    def predict_proba(self, X: np.ndarray) -> Optional[np.ndarray]:
        """Predict class probabilities if model supports it."""
        if hasattr(self.model, "predict_proba"):
            return self.model.predict_proba(X)
        return None

    def get_params(self) -> Dict[str, Any]:
        """Get model parameters."""
        if hasattr(self.model, "get_params"):
            return self.model.get_params()
        return {}


class SklearnEvaluator:
    """Evaluator using scikit-learn metrics."""

    def __init__(self, task_type: str = "classification"):
        """
        Initialize evaluator.

        Args:
            task_type: Either "classification" or "regression"
        """
        if task_type not in ["classification", "regression"]:
            raise ValueError(
                f"task_type must be 'classification' or 'regression', got {task_type}"
            )
        self.task_type = task_type

    def evaluate(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_proba: Optional[np.ndarray] = None,
    ) -> Dict[str, float]:
        """
        Evaluate predictions using appropriate metrics.

        Args:
            y_true: True labels
            y_pred: Predicted labels
            y_proba: Predicted probabilities (for classification)

        Returns:
            Dictionary of metric names and values
        """
        y_true_np, y_pred_np = ensure_numpy(y_true, y_pred)
        y_proba_np = ensure_numpy(y_proba)[0] if y_proba is not None else None

        if self.task_type == "classification":
            return self._evaluate_classification(y_true_np, y_pred_np, y_proba_np)
        else:
            return self._evaluate_regression(y_true_np, y_pred_np)

    def _evaluate_classification(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_proba: Optional[np.ndarray] = None,
    ) -> Dict[str, float]:
        """Compute classification metrics."""
        metrics = {}

        # Determine if binary or multiclass
        n_classes = len(np.unique(y_true))
        average = "binary" if n_classes == 2 else "weighted"

        # Basic metrics
        metrics["accuracy"] = accuracy_score(y_true, y_pred)
        metrics["precision"] = precision_score(
            y_true, y_pred, average=average, zero_division=0
        )
        metrics["recall"] = recall_score(
            y_true, y_pred, average=average, zero_division=0
        )
        metrics["f1_score"] = f1_score(y_true, y_pred, average=average, zero_division=0)

        # ROC AUC if probabilities are provided
        if y_proba is not None:
            try:
                if n_classes == 2:
                    # Binary: use positive class probabilities
                    metrics["roc_auc"] = roc_auc_score(y_true, y_proba[:, 1])
                else:
                    # Multiclass: use OvR approach
                    metrics["roc_auc"] = roc_auc_score(
                        y_true, y_proba, multi_class="ovr", average="weighted"
                    )
            except (ValueError, IndexError):
                # Skip if ROC AUC cannot be computed
                pass

        return metrics

    def _evaluate_regression(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
    ) -> Dict[str, float]:
        """Compute regression metrics."""
        metrics = {}

        metrics["mse"] = mean_squared_error(y_true, y_pred)
        metrics["rmse"] = np.sqrt(metrics["mse"])
        metrics["mae"] = mean_absolute_error(y_true, y_pred)
        metrics["r2"] = r2_score(y_true, y_pred)

        return metrics
