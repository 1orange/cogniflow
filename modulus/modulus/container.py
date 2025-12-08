"""Dependency injection container for wiring components."""

from typing import Dict, Any

from modulus.domain.entities import PipelineConfig
from modulus.application.pipeline_runner import PipelineRunner
from modulus.application.data_manager import DataManager
from modulus.application.preprocessing_manager import PreprocessingManager
from modulus.application.trainer import Trainer
from modulus.application.benchmark_manager import BenchmarkManager
from modulus.application.reporting_manager import ReportingManager
from modulus.infrastructure.loaders import NpyDataLoader


class DependencyContainer:
    """Container for dependency injection and component wiring."""

    @staticmethod
    def build_pipeline_runner(config: PipelineConfig) -> PipelineRunner:
        """
        Build and wire all pipeline components.

        Args:
            config: Complete pipeline configuration

        Returns:
            Fully configured PipelineRunner instance
        """
        # Build infrastructure components
        data_loader = DependencyContainer._build_data_loader(config.data_config)

        # Build application layer components
        data_manager = DataManager(data_loader)

        preprocessing_manager = PreprocessingManager(config.preprocessing_config)

        task_type = config.data_config.get("task_type", "classification")
        benchmark_manager = BenchmarkManager(task_type=task_type)

        trainer = Trainer()

        reporting_manager = ReportingManager()

        # Wire everything together in the pipeline runner
        pipeline_runner = PipelineRunner(
            data_manager=data_manager,
            preprocessing_manager=preprocessing_manager,
            trainer=trainer,
            benchmark_manager=benchmark_manager,
            reporting_manager=reporting_manager,
        )

        return pipeline_runner

    @staticmethod
    def _build_data_loader(data_config: Dict[str, Any]):
        """
        Build appropriate data loader based on configuration.

        Args:
            data_config: Data configuration dictionary

        Returns:
            Data loader instance
        """
        loader_type = data_config.get("loader", "npy")

        if loader_type == "npy":
            return NpyDataLoader(
                data_dir=data_config["source"],
                feature_key=data_config.get("feature_key", "features"),
                target_key=data_config.get("target_key", "labels"),
                metadata_key=data_config.get("metadata_key", "metadata"),
                use_metadata=data_config.get("use_metadata", False),
            )
        else:
            raise ValueError(f"Unsupported loader type: {loader_type}")
