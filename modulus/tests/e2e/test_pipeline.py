"""End-to-end pipeline tests."""

from pathlib import Path
import yaml

from modulus.config import ConfigLoader
from modulus.container import DependencyContainer
from modulus.domain.entities import PipelineConfig


class TestEndToEndPipeline:
    """End-to-end tests for complete pipeline."""

    def test_full_pipeline_execution(self, temp_dir, sample_npy_data):
        """Test complete pipeline execution from data to results."""

        # Create configuration
        config_dict = {
            "Data": {
                "source": sample_npy_data,
                "loader": "npy",
                "feature_key": "features",
                "target_key": "labels",
                "use_metadata": False,
                "task_type": "classification",
                "split": {
                    "train": 0.6,
                    "val": 0.2,
                    "test": 0.2,
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
                "path": str(Path(temp_dir) / "results"),
                "formats": ["csv", "json", "html"],
                "primary_metric": "accuracy",
            },
        }

        config = PipelineConfig.from_dict(config_dict)

        # Build and execute pipeline
        pipeline_runner = DependencyContainer.build_pipeline_runner(config)
        pipeline_runner.execute(config)

        # Verify outputs
        results_dir = Path(temp_dir) / "results"
        assert results_dir.exists()
        assert (results_dir / "results.csv").exists()
        assert (results_dir / "results.json").exists()
        assert (results_dir / "results.html").exists()
        assert (results_dir / "summary.txt").exists()

    def test_pipeline_with_multiple_models(self, temp_dir, sample_npy_data):
        """Test pipeline with multiple models."""

        config_dict = {
            "Data": {
                "source": sample_npy_data,
                "loader": "npy",
                "feature_key": "features",
                "target_key": "labels",
                "use_metadata": False,
                "split": {
                    "train": 0.6,
                    "val": 0.2,
                    "test": 0.2,
                    "random_state": 42,
                },
            },
            "Preprocessing": {
                "standard_scaler": True,
            },
            "Models": [
                {"name": "LogisticRegression", "params": {"max_iter": 100}},
                {"name": "RandomForest", "params": {"n_estimators": 10}},
            ],
            "Output": {
                "path": str(Path(temp_dir) / "results"),
                "formats": ["csv"],
            },
        }

        config = PipelineConfig.from_dict(config_dict)
        pipeline_runner = DependencyContainer.build_pipeline_runner(config)
        pipeline_runner.execute(config)

        # Check that results contain both models
        results_csv = Path(temp_dir) / "results" / "results.csv"
        with open(results_csv) as f:
            content = f.read()
            assert "LogisticRegression" in content
            assert "RandomForest" in content

    def test_config_from_file(self, temp_dir, sample_npy_data):
        """Test loading configuration from YAML file."""

        config_dict = {
            "Data": {
                "source": sample_npy_data,
                "loader": "npy",
                "feature_key": "features",
                "target_key": "labels",
                "use_metadata": False,
                "split": {
                    "train": 0.7,
                    "val": 0.15,
                    "test": 0.15,
                    "random_state": 42,
                },
            },
            "Preprocessing": {
                "standard_scaler": True,
            },
            "Models": [
                {"name": "LogisticRegression", "params": {"max_iter": 100}},
            ],
            "Output": {
                "path": str(Path(temp_dir) / "results"),
                "formats": ["csv"],
            },
        }

        # Write config to file
        config_path = Path(temp_dir) / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_dict, f)

        # Load config
        config = ConfigLoader.load_from_file(str(config_path))

        assert config.data_config["source"] == sample_npy_data
        assert len(config.model_specs) == 1
