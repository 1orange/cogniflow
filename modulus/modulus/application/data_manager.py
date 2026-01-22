"""Data management use case - loading and splitting."""

from typing import Optional
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from modulus.domain.entities import Dataset, Splits, SplitConfig
from modulus.domain.protocols import IDataLoader


class DataManager:
    """Manages data loading and splitting operations."""

    def __init__(self, data_loader: IDataLoader):
        """
        Initialize DataManager with a data loader.

        Args:
            data_loader: Implementation of IDataLoader protocol
        """
        self.data_loader = data_loader
        self._dataset: Optional[Dataset] = None

    def load(self) -> Dataset:
        """
        Load dataset using configured loader.

        Returns:
            Dataset entity with features, labels, and metadata
        """
        self._dataset = self.data_loader.load()
        return self._dataset

    def split(
        self,
        X: np.ndarray,
        y: np.ndarray,
        config: SplitConfig,
        metadata: Optional[pd.DataFrame] = None,
    ) -> Splits:
        """
        Split data into train/validation/test sets.

        Args:
            X: Feature matrix
            y: Label array
            config: Split configuration (ratios, random_state, etc.)
            metadata: Optional metadata DataFrame

        Returns:
            Splits entity with train/val/test data
        """
        # Validate inputs
        if len(X) != len(y):
            raise ValueError(f"X and y length mismatch: {len(X)} vs {len(y)}")

        # First split: train+val vs test
        test_size = config.test
        train_val_size = config.train + config.val

        stratify_y = y if config.stratify else None

        X_trainval, X_test, y_trainval, y_test = train_test_split(
            X,
            y,
            test_size=test_size,
            random_state=config.random_state,
            stratify=stratify_y,
        )

        # Second split: train vs val
        val_ratio = config.val / train_val_size

        # Re-stratify on the trainval subset
        stratify_trainval = y_trainval if config.stratify else None

        X_train, X_val, y_train, y_val = train_test_split(
            X_trainval,
            y_trainval,
            test_size=val_ratio,
            random_state=config.random_state,
            stratify=stratify_trainval,
        )

        # Handle metadata splitting if provided
        metadata_train = None
        metadata_val = None
        metadata_test = None

        if metadata is not None:
            # Get indices for splits (this requires re-implementation with indices)
            indices = np.arange(len(X))

            idx_trainval, idx_test = train_test_split(
                indices,
                test_size=test_size,
                random_state=config.random_state,
                stratify=stratify_y,
            )

            idx_train, idx_val = train_test_split(
                idx_trainval,
                test_size=val_ratio,
                random_state=config.random_state,
                stratify=y[idx_trainval] if config.stratify else None,
            )

            metadata_train = metadata.iloc[idx_train].reset_index(drop=True)
            metadata_val = metadata.iloc[idx_val].reset_index(drop=True)
            metadata_test = metadata.iloc[idx_test].reset_index(drop=True)

        return Splits(
            X_train=X_train,
            X_val=X_val,
            X_test=X_test,
            y_train=y_train,
            y_val=y_val,
            y_test=y_test,
            metadata_train=metadata_train,
            metadata_val=metadata_val,
            metadata_test=metadata_test,
        )
