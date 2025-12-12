"""Unit tests for PreprocessingManager."""

import pytest
import numpy as np

from modulus.application.preprocessing_manager import PreprocessingManager


class TestPreprocessingManager:
    """Tests for PreprocessingManager."""

    def test_build_with_standard_scaler(self):
        """Test building pipeline with standard scaler."""
        config = {"standard_scaler": True}
        manager = PreprocessingManager(config)

        pipeline = manager.build()

        assert len(pipeline.steps) > 0
        assert any("scaler" in name for name, _ in pipeline.steps)

    def test_build_with_pca(self):
        """Test building pipeline with PCA."""
        config = {"standard_scaler": False, "pca_components": 5}
        manager = PreprocessingManager(config)

        pipeline = manager.build()

        assert any("pca" in name for name, _ in pipeline.steps)

    def test_fit_transform(self):
        """Test fit_transform functionality."""
        X = np.random.randn(100, 10)
        config = {"standard_scaler": True}

        manager = PreprocessingManager(config)
        manager.build()
        X_transformed = manager.fit_transform(X)

        assert X_transformed.shape == X.shape
        # Check that data is standardized
        assert np.abs(X_transformed.mean()) < 0.1
        assert np.abs(X_transformed.std() - 1.0) < 0.1

    def test_transform_without_fit_raises_error(self):
        """Test that transform without fit raises error."""
        X = np.random.randn(100, 10)
        config = {"standard_scaler": True}

        manager = PreprocessingManager(config)

        with pytest.raises(RuntimeError, match="not built or fitted"):
            manager.transform(X)

    def test_empty_pipeline(self):
        """Test that empty config creates passthrough pipeline."""
        config = {}
        manager = PreprocessingManager(config)

        pipeline = manager.build()

        assert len(pipeline.steps) > 0  # At least passthrough
