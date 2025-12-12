"""Integration tests for NPY data loader."""

import pytest
import numpy as np
from pathlib import Path

from modulus.infrastructure.loaders import NpyDataLoader


class TestNpyDataLoader:
    """Integration tests for NpyDataLoader."""

    def test_load_single_file(self, temp_dir):
        """Test loading a single .npy file."""
        data_dir = Path(temp_dir) / "data"
        data_dir.mkdir()

        # Create test data
        data = {
            "features": np.random.randn(50, 10),
            "labels": np.random.randint(0, 2, 50),
        }
        np.save(data_dir / "data.npy", data)

        loader = NpyDataLoader(str(data_dir))
        dataset = loader.load()

        assert len(dataset.X) == 50
        assert dataset.X.shape[1] == 10
        assert len(dataset.y) == 50

    def test_load_multiple_files(self, sample_npy_data):
        """Test loading and concatenating multiple .npy files."""
        loader = NpyDataLoader(sample_npy_data)
        dataset = loader.load()

        # 3 files * 30 samples = 90 total
        assert len(dataset.X) == 90
        assert len(dataset.y) == 90

    def test_load_with_metadata(self, sample_npy_data):
        """Test loading with metadata."""
        loader = NpyDataLoader(sample_npy_data, use_metadata=False)
        dataset = loader.load()

        assert dataset.metadata is not None
        assert len(dataset.metadata) == 90

    def test_missing_feature_key(self, temp_dir):
        """Test that missing feature key raises error."""
        data_dir = Path(temp_dir) / "data"
        data_dir.mkdir()

        # Create data without features key
        data = {"labels": np.array([0, 1])}
        np.save(data_dir / "data.npy", data)

        loader = NpyDataLoader(str(data_dir))

        with pytest.raises(KeyError, match="Feature key"):
            loader.load()

    def test_nonexistent_directory(self):
        """Test that nonexistent directory raises error."""
        with pytest.raises(FileNotFoundError):
            NpyDataLoader("/nonexistent/path")

    def test_empty_directory(self, temp_dir):
        """Test that empty directory raises error."""
        data_dir = Path(temp_dir) / "empty"
        data_dir.mkdir()

        loader = NpyDataLoader(str(data_dir))

        with pytest.raises(ValueError, match="No .npy files"):
            loader.load()
