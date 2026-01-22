"""Integration tests for Trainer."""

import pytest
import numpy as np

from modulus.application.trainer import Trainer
from modulus.domain.entities import ModelSpec


class TestTrainer:
    """Integration tests for Trainer."""

    def test_fit_single_model(self):
        """Test training a single model."""
        X_train = np.random.randn(100, 10)
        y_train = np.random.randint(0, 2, 100)

        specs = [ModelSpec(name="LogisticRegression", params={"max_iter": 100})]

        trainer = Trainer()
        pipelines = trainer.fit_all(specs, X_train, y_train)

        assert len(pipelines) == 1
        assert "LogisticRegression" in pipelines

    def test_fit_multiple_models(self, model_specs):
        """Test training multiple models."""
        X_train = np.random.randn(100, 10)
        y_train = np.random.randint(0, 2, 100)

        trainer = Trainer()
        pipelines = trainer.fit_all(model_specs, X_train, y_train)

        assert len(pipelines) == 2
        assert "LogisticRegression" in pipelines
        assert "RandomForest" in pipelines

    def test_predict_all(self, model_specs):
        """Test predictions from multiple models."""
        X_train = np.random.randn(100, 10)
        y_train = np.random.randint(0, 2, 100)
        X_test = np.random.randn(20, 10)

        trainer = Trainer()
        pipelines = trainer.fit_all(model_specs, X_train, y_train)
        predictions, probabilities = trainer.predict_all(pipelines, X_test)

        assert len(predictions) == 2
        assert len(predictions["LogisticRegression"]) == 20
        assert probabilities["LogisticRegression"] is not None

    def test_unknown_model(self):
        """Test that unknown model raises error."""
        specs = [ModelSpec(name="UnknownModel")]
        trainer = Trainer()

        with pytest.raises(ValueError, match="Unknown model"):
            trainer.fit_all(specs, np.array([[1]]), np.array([0]))
