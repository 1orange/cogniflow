"""Benchmark and evaluation management."""

from typing import List, Dict, Optional
import numpy as np

from modulus.domain.entities import MetricSet
from modulus.infrastructure.ml.sklearn_adapter import SklearnEvaluator


class BenchmarkManager:
    """Manages model evaluation and benchmarking."""

    def __init__(self, task_type: str = "classification"):
        """
        Initialize benchmark manager.

        Args:
            task_type: Either "classification" or "regression"
        """
        self.task_type = task_type
        self.evaluator = SklearnEvaluator(task_type=task_type)

    def evaluate_all(
        self,
        y_true: np.ndarray,
        predictions: Dict[str, np.ndarray],
        probabilities: Dict[str, Optional[np.ndarray]],
        split_name: str = "validation",
    ) -> List[MetricSet]:
        """
        Evaluate all model predictions.

        Args:
            y_true: True labels
            predictions: Dictionary of model predictions
            probabilities: Dictionary of model probabilities
            split_name: Name of the split being evaluated

        Returns:
            List of MetricSet entities with evaluation results
        """
        metric_sets = []

        for model_name, y_pred in predictions.items():
            y_proba = probabilities.get(model_name)

            # Evaluate using the evaluator
            metrics = self.evaluator.evaluate(y_true, y_pred, y_proba)

            # Create MetricSet entity
            metric_set = MetricSet(
                model_name=model_name,
                metrics=metrics,
                split=split_name,
            )
            metric_sets.append(metric_set)

        return metric_sets

    def rank_models(
        self,
        metric_sets: List[MetricSet],
        primary_metric: str = "accuracy",
    ) -> List[MetricSet]:
        """
        Rank models by a primary metric.

        Args:
            metric_sets: List of MetricSet entities
            primary_metric: Metric to rank by (higher is better)

        Returns:
            Sorted list of MetricSet entities
        """
        # Sort by primary metric (descending)
        sorted_metrics = sorted(
            metric_sets,
            key=lambda ms: ms.get_metric(primary_metric, -np.inf),
            reverse=True,
        )

        return sorted_metrics

    def summarize(self, metric_sets: List[MetricSet]) -> Dict[str, Dict[str, float]]:
        """
        Create summary statistics across models.

        Args:
            metric_sets: List of MetricSet entities

        Returns:
            Dictionary with summary statistics
        """
        if not metric_sets:
            return {}

        # Collect all metrics
        all_metrics = {}
        for ms in metric_sets:
            all_metrics[ms.model_name] = ms.metrics

        return all_metrics
