"""Pytest configuration and fixtures."""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import shutil

from modulus.domain.entities import Dataset, SplitConfig, ModelSpec


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_dataset():
    """Create a sample dataset for testing."""
    np.random.seed(42)
    X = np.random.randn(100, 10)
    y = np.random.randint(0, 2, 100)
    metadata = pd.DataFrame(
        {
            "id": range(100),
            "category": np.random.choice(["A", "B", "C"], 100),
            "value": np.random.randn(100),
        }
    )
    return Dataset(X=X, y=y, metadata=metadata)


@pytest.fixture
def sample_npy_data(temp_dir):
    """Create sample .npy files for testing."""
    data_dir = Path(temp_dir) / "data"
    data_dir.mkdir()

    # Create multiple .npy files
    for i in range(3):
        data = {
            "features": np.random.randn(30, 10),
            "labels": np.random.randint(0, 2, 30),
            "metadata": pd.DataFrame(
                {
                    "id": range(i * 30, (i + 1) * 30),
                    "batch": [i] * 30,
                }
            ),
        }
        np.save(data_dir / f"data_{i}.npy", data)

    return str(data_dir)


@pytest.fixture
def split_config():
    """Create a sample split configuration."""
    return SplitConfig(
        train=0.7,
        val=0.15,
        test=0.15,
        random_state=42,
        stratify=True,
    )


@pytest.fixture
def model_specs():
    """Create sample model specifications."""
    return [
        ModelSpec(name="LogisticRegression", params={"max_iter": 100}),
        ModelSpec(name="RandomForest", params={"n_estimators": 10, "random_state": 42}),
    ]


@pytest.fixture
def pipeline_config():
    """Create a sample pipeline configuration."""
    return {
        "Data": {
            "source": "data/",
            "loader": "npy",
            "feature_key": "features",
            "target_key": "labels",
            "use_metadata": False,
            "split": {
                "train": 0.7,
                "val": 0.15,
                "test": 0.15,
                "random_state": 42,
                "stratify": True,
            },
        },
        "Preprocessing": {
            "standard_scaler": True,
            "pca_components": None,
        },
        "Models": [
            {"name": "LogisticRegression", "params": {"max_iter": 100}},
        ],
        "Output": {
            "path": "results/",
            "formats": ["csv"],
            "primary_metric": "accuracy",
        },
    }
