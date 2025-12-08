"""Model training orchestration."""

from typing import List, Dict, Tuple, Optional, Any
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline

from modulus.domain.entities import ModelSpec


class Trainer:
    """Orchestrates model training for multiple models."""

    # Model registry mapping names to classes
    MODEL_REGISTRY = {
        "LogisticRegression": LogisticRegression,
        "RandomForest": RandomForestClassifier,
        "RandomForestClassifier": RandomForestClassifier,
        "GradientBoosting": GradientBoostingClassifier,
        "GradientBoostingClassifier": GradientBoostingClassifier,
        "SVC": SVC,
        "SVM": SVC,
        "DecisionTree": DecisionTreeClassifier,
        "DecisionTreeClassifier": DecisionTreeClassifier,
        "NaiveBayes": GaussianNB,
        "GaussianNB": GaussianNB,
        "KNN": KNeighborsClassifier,
        "KNeighborsClassifier": KNeighborsClassifier,
    }

    def __init__(self):
        """Initialize trainer."""
        self.trained_models: Dict[str, Any] = {}

    def fit_all(
        self,
        model_specs: List[ModelSpec],
        X_train: np.ndarray,
        y_train: np.ndarray,
        preprocessor: Optional[Pipeline] = None,
    ) -> Dict[str, Pipeline]:
        """
        Train all specified models.

        Args:
            model_specs: List of model specifications
            X_train: Training features
            y_train: Training labels
            preprocessor: Optional preprocessing pipeline

        Returns:
            Dictionary mapping model names to trained pipelines
        """
        pipelines = {}

        for spec in model_specs:
            print(f"Training {spec.name}...")

            # Create model instance
            model = self._create_model(spec)

            # Create pipeline with preprocessor if provided
            if preprocessor is not None:
                pipeline = Pipeline(
                    [
                        ("preprocessor", preprocessor),
                        ("model", model),
                    ]
                )
            else:
                pipeline = Pipeline([("model", model)])

            # Train the pipeline
            pipeline.fit(X_train, y_train)
            pipelines[spec.name] = pipeline

            self.trained_models[spec.name] = pipeline

        return pipelines

    def predict_all(
        self,
        pipelines: Dict[str, Pipeline],
        X: np.ndarray,
    ) -> Tuple[Dict[str, np.ndarray], Dict[str, Optional[np.ndarray]]]:
        """
        Generate predictions from all trained models.

        Args:
            pipelines: Dictionary of trained pipelines
            X: Features to predict on

        Returns:
            Tuple of (predictions dict, probabilities dict)
        """
        predictions = {}
        probabilities = {}

        for name, pipeline in pipelines.items():
            # Get predictions
            predictions[name] = pipeline.predict(X)

            # Get probabilities if available
            if hasattr(pipeline.named_steps["model"], "predict_proba"):
                probabilities[name] = pipeline.predict_proba(X)
            else:
                probabilities[name] = None

        return predictions, probabilities

    def _create_model(self, spec: ModelSpec) -> Any:
        """
        Create a model instance from specification.

        Args:
            spec: Model specification

        Returns:
            Instantiated model object
        """
        if spec.name not in self.MODEL_REGISTRY:
            raise ValueError(
                f"Unknown model: {spec.name}. "
                f"Available models: {list(self.MODEL_REGISTRY.keys())}"
            )

        model_class = self.MODEL_REGISTRY[spec.name]

        # Handle probability=True for SVC
        params = spec.params.copy()
        if model_class == SVC and "probability" not in params:
            params["probability"] = True

        return model_class(**params)
