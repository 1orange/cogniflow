"""Unit tests for domain entities."""

import pytest
import numpy as np
import pandas as pd

from modulus.domain.entities import (
    Dataset,
    SplitConfig,
    ModelSpec,
    MetricSet,
    PipelineConfig,
)


class TestDataset:
    """Tests for Dataset entity."""

    def test_valid_dataset(self):
        """Test creating a valid dataset."""
        X = np.array([[1, 2], [3, 4]])
        y = np.array([0, 1])
        dataset = Dataset(X=X, y=y)

        assert len(dataset.X) == 2
        assert len(dataset.y) == 2
        assert dataset.metadata is None

    def test_dataset_with_metadata(self):
        """Test dataset with metadata."""
        X = np.array([[1, 2], [3, 4]])
        y = np.array([0, 1])
        metadata = pd.DataFrame({"id": [1, 2]})

        dataset = Dataset(X=X, y=y, metadata=metadata)

        assert dataset.metadata is not None
        assert len(dataset.metadata) == 2

    def test_dataset_dimension_mismatch(self):
        """Test that dimension mismatch raises error."""
        X = np.array([[1, 2], [3, 4]])
        y = np.array([0])  # Wrong size

        with pytest.raises(ValueError, match="mismatch"):
            Dataset(X=X, y=y)

    def test_metadata_length_mismatch(self):
        """Test that metadata length mismatch raises error."""
        X = np.array([[1, 2], [3, 4]])
        y = np.array([0, 1])
        metadata = pd.DataFrame({"id": [1]})  # Wrong size

        with pytest.raises(ValueError, match="Metadata length mismatch"):
            Dataset(X=X, y=y, metadata=metadata)


class TestSplitConfig:
    """Tests for SplitConfig entity."""

    def test_valid_split_config(self):
        """Test creating valid split configuration."""
        config = SplitConfig(train=0.7, val=0.15, test=0.15)

        assert config.train == 0.7
        assert config.val == 0.15
        assert config.test == 0.15
        assert config.random_state == 42

    def test_invalid_split_ratios(self):
        """Test that invalid ratios raise error."""
        with pytest.raises(ValueError, match="sum to 1.0"):
            SplitConfig(train=0.5, val=0.3, test=0.3)

    def test_negative_split_ratio(self):
        """Test that negative ratios raise error."""
        with pytest.raises(ValueError, match="positive"):
            SplitConfig(train=0.8, val=-0.1, test=0.3)


class TestModelSpec:
    """Tests for ModelSpec entity."""

    def test_valid_model_spec(self):
        """Test creating valid model specification."""
        spec = ModelSpec(name="LogisticRegression", params={"C": 1.0})

        assert spec.name == "LogisticRegression"
        assert spec.params["C"] == 1.0

    def test_empty_name(self):
        """Test that empty name raises error."""
        with pytest.raises(ValueError, match="cannot be empty"):
            ModelSpec(name="", params={})

    def test_default_params(self):
        """Test default empty params."""
        spec = ModelSpec(name="RandomForest")

        assert spec.params == {}


class TestMetricSet:
    """Tests for MetricSet entity."""

    def test_valid_metric_set(self):
        """Test creating valid metric set."""
        metrics = {"accuracy": 0.95, "f1_score": 0.92}
        metric_set = MetricSet(
            model_name="LogisticRegression",
            metrics=metrics,
            split="validation",
        )

        assert metric_set.model_name == "LogisticRegression"
        assert metric_set.get_metric("accuracy") == 0.95
        assert metric_set.split == "validation"

    def test_get_missing_metric(self):
        """Test retrieving missing metric returns default."""
        metric_set = MetricSet(
            model_name="Model",
            metrics={"accuracy": 0.9},
        )

        assert metric_set.get_metric("missing", default=0.0) == 0.0

    def test_repr(self):
        """Test string representation."""
        metric_set = MetricSet(
            model_name="Model",
            metrics={"acc": 0.5},
            split="test",
        )

        repr_str = repr(metric_set)
        assert "Model" in repr_str
        assert "test" in repr_str


class TestPipelineConfig:
    """Tests for PipelineConfig entity."""

    def test_from_dict(self):
        """Test creating config from dictionary."""
        config_dict = {
            "Data": {"source": "data/"},
            "Preprocessing": {"standard_scaler": True},
            "Models": [
                {"name": "LogisticRegression", "params": {"C": 1.0}},
            ],
            "Output": {"path": "results/"},
        }

        config = PipelineConfig.from_dict(config_dict)

        assert len(config.model_specs) == 1
        assert config.model_specs[0].name == "LogisticRegression"
        assert config.data_config["source"] == "data/"
