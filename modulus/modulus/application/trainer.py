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
from modulus.infrastructure.ml.gpu_utils import (
    detect_gpu_stack,
    to_cpu_array,
)


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

    GPU_MODEL_REGISTRY = {
        # Map model name to a callable that returns the cuML class
        "LogisticRegression": lambda cuml: cuml.linear_model.LogisticRegression,
        "RandomForest": lambda cuml: cuml.ensemble.RandomForestClassifier,
        "RandomForestClassifier": lambda cuml: cuml.ensemble.RandomForestClassifier,
        "SVC": lambda cuml: cuml.svm.SVC,
        "SVM": lambda cuml: cuml.svm.SVC,
        "KNN": lambda cuml: cuml.neighbors.KNeighborsClassifier,
        "KNeighborsClassifier": lambda cuml: cuml.neighbors.KNeighborsClassifier,
    }

    def __init__(self, use_gpu: bool = False, device_id: Optional[int] = None):
        """Initialize trainer."""
        self.trained_models: Dict[str, Any] = {}
        self.use_gpu = use_gpu
        self.device_id = device_id
        self._gpu_state = detect_gpu_stack(device_id) if use_gpu else {"available": False}
        # Track which models are actually using GPU backends
        self._model_use_gpu: Dict[str, bool] = {}

        if self.use_gpu and not self._gpu_state.get("available"):
            # Graceful fallback to CPU if GPU stack is missing
            fallback_reason = self._gpu_state.get("error") or "GPU stack not available"
            print(f"[Trainer] GPU requested but unavailable: {fallback_reason}. Falling back to CPU.")
            self.use_gpu = False
        elif self.use_gpu:
            device_name = self._gpu_state.get("device") or "CUDA device"
            print(f"[Trainer] Using GPU backend on {device_name} (cuML).")

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
            # Create model instance
            model, model_is_gpu = self._create_model(spec)
            self._model_use_gpu[spec.name] = model_is_gpu

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
            X_fit = X_train
            y_fit = y_train
            if self.use_gpu and not model_is_gpu:
                # CPU model but data is likely on GPU; bring back to CPU
                X_fit = self._to_numpy(X_train)
                y_fit = self._to_numpy(y_train)

            pipeline.fit(X_fit, y_fit)
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
            model_is_gpu = self._model_use_gpu.get(name, False)
            X_input = X
            if self.use_gpu and not model_is_gpu:
                X_input = self._to_numpy(X)

            # Get predictions
            predictions[name] = self._to_numpy(pipeline.predict(X_input))

            # Get probabilities if available
            if hasattr(pipeline.named_steps["model"], "predict_proba"):
                probabilities[name] = self._to_numpy(pipeline.predict_proba(X_input))
            else:
                probabilities[name] = None

        return predictions, probabilities

    def _create_model(self, spec: ModelSpec) -> tuple[Any, bool]:
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

        params = spec.params.copy()

        # Prefer GPU backend if requested and available
        if self.use_gpu and self._gpu_state.get("available"):
            gpu_factory = self.GPU_MODEL_REGISTRY.get(spec.name)
            if gpu_factory:
                cuml = self._gpu_state["cuml"]
                model_class = gpu_factory(cuml)
                print(f"[Trainer] {spec.name}: cuML backend enabled.")
                # Drop params unsupported by cuML
                params.pop("random_state", None)
                params.pop("n_jobs", None)
                return model_class(**params), True
            else:
                print(f"[Trainer] GPU requested but {spec.name} not available in cuML. Using CPU model.")

        model_class = self.MODEL_REGISTRY[spec.name]

        # Handle probability=True for SVC (sklearn only)
        if model_class == SVC and "probability" not in params:
            params["probability"] = True

        return model_class(**params), False

    def _to_numpy(self, array: Any) -> np.ndarray:
        """Convert CuPy/cuDF outputs to numpy for downstream metrics."""
        array = to_cpu_array(array)
        if hasattr(array, "to_numpy"):
            try:
                return array.to_numpy()
            except Exception:  # noqa: BLE001
                pass
        if hasattr(array, "values"):
            try:
                return np.asarray(array.values)
            except Exception:  # noqa: BLE001
                pass
        return np.asarray(array)
