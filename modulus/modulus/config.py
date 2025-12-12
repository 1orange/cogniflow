"""Configuration loading and validation."""

from pathlib import Path
from typing import Dict, Any
import yaml

from modulus.domain.entities import PipelineConfig


class ConfigLoader:
    """Loads and validates pipeline configuration from YAML files."""

    @staticmethod
    def load_from_file(config_path: str) -> PipelineConfig:
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to YAML configuration file

        Returns:
            PipelineConfig entity
        """
        config_file = Path(config_path)

        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_file, "r") as f:
            config_dict = yaml.safe_load(f)

        # Validate required sections
        ConfigLoader._validate_config(config_dict)

        return PipelineConfig.from_dict(config_dict)

    @staticmethod
    def _validate_config(config_dict: Dict[str, Any]) -> None:
        """
        Validate configuration structure.

        Args:
            config_dict: Configuration dictionary

        Raises:
            ValueError: If configuration is invalid
        """
        required_sections = ["Data", "Models", "Output"]

        for section in required_sections:
            if section not in config_dict:
                raise ValueError(f"Missing required configuration section: {section}")

        # Validate Data section
        data_config = config_dict["Data"]
        if "source" not in data_config:
            raise ValueError("Data section must contain 'source' field")

        # Validate Models section
        models = config_dict["Models"]
        if not models or len(models) == 0:
            raise ValueError("Models section must contain at least one model")

        for model in models:
            if "name" not in model:
                raise ValueError("Each model must have a 'name' field")

    @staticmethod
    def get_default_config() -> Dict[str, Any]:
        """
        Get a default configuration template.

        Returns:
            Dictionary with default configuration
        """
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
                {
                    "name": "LogisticRegression",
                    "params": {"max_iter": 1000},
                },
                {
                    "name": "RandomForest",
                    "params": {"n_estimators": 100, "random_state": 42},
                },
            ],
            "Output": {
                "path": "results/",
                "formats": ["csv", "json", "html"],
                "primary_metric": "accuracy",
            },
            "Compute": {
                # When true and GPU stack is available, use cuML/CuPy backends
                "use_gpu": False,
                # Optional CUDA device id to select; defaults to primary device
                "device_id": None,
            },
        }
