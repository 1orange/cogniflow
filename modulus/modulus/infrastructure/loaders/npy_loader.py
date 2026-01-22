"""Data loader for .npy files with embedded metadata."""

from pathlib import Path
from typing import Optional
import numpy as np
import pandas as pd

from modulus.domain.entities import Dataset


class NpyDataLoader:
    """Loads datasets from multiple .npy files with embedded dictionaries."""

    def __init__(
        self,
        data_dir: str,
        feature_key: str = "features",
        target_key: str = "labels",
        metadata_key: str = "metadata",
        use_metadata: bool = False,
        specific_file: Optional[str] = None,
    ):
        """
        Initialize the NPY data loader.

        Args:
            data_dir: Directory containing .npy files OR path to specific .npy file
            feature_key: Key for feature arrays in .npy dictionaries
            target_key: Key for label arrays in .npy dictionaries
            metadata_key: Key for metadata in .npy dictionaries
            use_metadata: Whether to include metadata as additional features
            specific_file: If provided, only load this specific filename from data_dir
        """
        self.data_dir = Path(data_dir)
        self.feature_key = feature_key
        self.target_key = target_key
        self.metadata_key = metadata_key
        self.use_metadata = use_metadata
        self.specific_file = specific_file

        # If data_dir is actually a file, extract directory and filename
        if self.data_dir.is_file():
            self.specific_file = self.data_dir.name
            self.data_dir = self.data_dir.parent

        if not self.data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {data_dir}")

    def load(self) -> Dataset:
        """
        Load and concatenate all .npy files (or specific file) into a Dataset.

        Returns:
            Dataset entity with features, labels, and optional metadata
        """
        # Load specific file if specified, otherwise load all
        if self.specific_file:
            npy_files = [self.data_dir / self.specific_file]
            if not npy_files[0].exists():
                raise FileNotFoundError(f"Specific file not found: {npy_files[0]}")
        else:
            npy_files = sorted(self.data_dir.glob("*.npy"))

        if not npy_files:
            raise ValueError(f"No .npy files found in {self.data_dir}")

        all_features = []
        all_labels = []
        all_metadata = []

        for npy_file in npy_files:
            data = self._load_single_file(npy_file)

            # Validate required keys
            if self.feature_key not in data:
                raise KeyError(
                    f"Feature key '{self.feature_key}' not found in {npy_file}"
                )
            if self.target_key not in data:
                raise KeyError(
                    f"Target key '{self.target_key}' not found in {npy_file}"
                )

            all_features.append(data[self.feature_key])
            all_labels.append(data[self.target_key])

            # Handle metadata if present
            if self.metadata_key in data and data[self.metadata_key] is not None:
                metadata = data[self.metadata_key]
                if isinstance(metadata, dict):
                    metadata = pd.DataFrame([metadata] * len(data[self.feature_key]))
                elif isinstance(metadata, pd.DataFrame):
                    pass
                elif isinstance(metadata, np.ndarray):
                    metadata = pd.DataFrame(metadata)
                else:
                    metadata = pd.DataFrame(metadata)
                all_metadata.append(metadata)

        # Concatenate all data
        X = (
            np.vstack(all_features)
            if len(all_features[0].shape) > 1
            else np.concatenate(all_features)
        )
        y = np.concatenate(all_labels)

        # Merge metadata if available
        metadata_df = None
        if all_metadata:
            metadata_df = pd.concat(all_metadata, ignore_index=True)

            # Optionally merge numerical metadata into features
            if self.use_metadata:
                numeric_cols = metadata_df.select_dtypes(include=[np.number]).values
                if numeric_cols.size > 0:
                    X = np.hstack([X, numeric_cols])

        return Dataset(X=X, y=y, metadata=metadata_df)

    def _load_single_file(self, filepath: Path) -> dict:
        """
        Load a single .npy file.

        Args:
            filepath: Path to .npy file

        Returns:
            Dictionary containing features, labels, and metadata
        """
        try:
            # Load with allow_pickle for dictionary support
            data = np.load(filepath, allow_pickle=True).item()

            if not isinstance(data, dict):
                raise TypeError(f"Expected dictionary in {filepath}, got {type(data)}")

            return data
        except Exception as e:
            raise RuntimeError(f"Failed to load {filepath}: {e}") from e
