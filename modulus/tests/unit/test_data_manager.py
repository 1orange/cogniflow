"""Unit tests for DataManager."""

import pytest
import numpy as np

from modulus.application.data_manager import DataManager


class TestDataManager:
    """Tests for DataManager."""

    def test_load_dataset(self, sample_dataset):
        """Test loading dataset through mock loader."""

        class MockLoader:
            def load(self):
                return sample_dataset

        manager = DataManager(MockLoader())
        dataset = manager.load()

        assert len(dataset.X) == 100
        assert len(dataset.y) == 100

    def test_split_data(self, sample_dataset, split_config):
        """Test data splitting."""

        class MockLoader:
            def load(self):
                return sample_dataset

        manager = DataManager(MockLoader())
        splits = manager.split(
            sample_dataset.X,
            sample_dataset.y,
            split_config,
        )

        # Check split sizes
        total = len(splits.X_train) + len(splits.X_val) + len(splits.X_test)
        assert total == 100

        # Check approximate ratios
        assert len(splits.X_train) == 70
        assert len(splits.X_val) == 15
        assert len(splits.X_test) == 15

    def test_split_with_metadata(self, sample_dataset, split_config):
        """Test splitting with metadata."""

        class MockLoader:
            def load(self):
                return sample_dataset

        manager = DataManager(MockLoader())
        splits = manager.split(
            sample_dataset.X,
            sample_dataset.y,
            split_config,
            metadata=sample_dataset.metadata,
        )

        assert splits.metadata_train is not None
        assert len(splits.metadata_train) == len(splits.X_train)
        assert len(splits.metadata_val) == len(splits.X_val)
        assert len(splits.metadata_test) == len(splits.X_test)

    def test_split_dimension_mismatch(self, split_config):
        """Test that dimension mismatch raises error."""

        class MockLoader:
            def load(self):
                pass

        manager = DataManager(MockLoader())
        X = np.array([[1, 2], [3, 4]])
        y = np.array([0])  # Wrong size

        with pytest.raises(ValueError, match="mismatch"):
            manager.split(X, y, split_config)
