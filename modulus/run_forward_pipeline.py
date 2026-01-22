#!/usr/bin/env python3
"""
Run the modulus pipeline on forward direction data with custom preprocessing.

This script demonstrates how to:
1. Prepare data in the format expected by modulus
2. Use custom preprocessing techniques
3. Train multiple models
4. Compare results

Usage:
    # Prepare data (run once)
    poetry run python prepare_direction_data.py --mode multiclass

    # Run pipeline
    poetry run python run_forward_pipeline.py

    # Or with custom config
    poetry run python run_forward_pipeline.py --config config/forward_direction_config.yaml
"""

import argparse
import sys
from pathlib import Path

from modulus.domain.entities import PipelineConfig, ModelSpec
from modulus.infrastructure.loaders.npy_loader import NpyDataLoader
from modulus.application.data_manager import DataManager
from modulus.application.extended_preprocessing_manager import (
    ExtendedPreprocessingManager,
)
from modulus.application.trainer import Trainer
from modulus.application.benchmark_manager import BenchmarkManager
from modulus.application.reporting_manager import ReportingManager
from modulus.application.pipeline_runner import PipelineRunner


def build_pipeline_with_custom_preprocessing(config_dict: dict) -> PipelineRunner:
    """
    Build pipeline with custom preprocessing support.

    This is similar to the standard DependencyContainer.build_pipeline_runner()
    but uses ExtendedPreprocessingManager instead of PreprocessingManager.

    Args:
        config_dict: Configuration dictionary

    Returns:
        Configured PipelineRunner
    """
    # Parse config
    data_config = config_dict.get("Data", {})
    preprocessing_config = config_dict.get("Preprocessing", {})
    model_configs = config_dict.get("Models", [])
    output_config = config_dict.get("Output", {})

    # 1. Create data loader
    print("\n1. Setting up data loader...")
    data_loader = NpyDataLoader(
        data_dir=data_config.get("source", "data/"),
        feature_key=data_config.get("feature_key", "features"),
        target_key=data_config.get("target_key", "labels"),
        metadata_key=data_config.get("metadata_key", "metadata"),
        use_metadata=data_config.get("use_metadata", False),
    )

    # 2. Create data manager
    data_manager = DataManager(data_loader)

    # 3. Create extended preprocessing manager with time-series support
    print("2. Setting up extended preprocessing manager...")

    # For forward data: 192 timesteps, 14 channels
    # For downsampled: adjust accordingly
    preprocessing_manager = ExtendedPreprocessingManager(
        config=preprocessing_config,
        n_timesteps=192,  # Will be auto-detected if not specified
        n_channels=14,
    )

    # 4. Create trainer
    print("3. Setting up model trainer...")
    trainer = Trainer()

    # 5. Create benchmark manager
    print("4. Setting up benchmark manager...")
    benchmark_manager = BenchmarkManager()

    # 6. Create reporting manager
    print("5. Setting up reporting manager...")
    reporting_manager = ReportingManager()

    # 7. Create pipeline runner
    print("6. Creating pipeline runner...")
    pipeline_runner = PipelineRunner(
        data_manager=data_manager,
        preprocessing_manager=preprocessing_manager,
        trainer=trainer,
        benchmark_manager=benchmark_manager,
        reporting_manager=reporting_manager,
    )

    return pipeline_runner


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Run modulus ML pipeline on forward direction data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default config
  poetry run python run_forward_pipeline.py
  
  # Run with custom config
  poetry run python run_forward_pipeline.py --config config/forward_direction_config.yaml
  
  # Prepare data first (if not already done)
  poetry run python prepare_direction_data.py --mode multiclass
        """,
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config/forward_direction_config.yaml",
        help="Path to YAML configuration file",
    )

    parser.add_argument(
        "--prepare-data",
        action="store_true",
        help="Prepare data before running pipeline",
    )

    args = parser.parse_args()

    # Check if config file exists
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Configuration file not found: {config_path}", file=sys.stderr)
        print("\nTip: Generate a default config with:")
        print("  python -m modulus.cli --generate-config")
        return 1

    # Optionally prepare data
    if args.prepare_data:
        print("Preparing data...")
        from prepare_direction_data import prepare_all_directions_multiclass

        prepare_all_directions_multiclass()
        print()

    # Check if prepared data exists
    data_file = Path("data/prepared/directions_multiclass.npy")
    if not data_file.exists():
        print("Error: Prepared data not found!")
        print("\nPlease run data preparation first:")
        print("  poetry run python prepare_direction_data.py --mode multiclass")
        print("\nOr run with --prepare-data flag:")
        print("  poetry run python run_forward_pipeline.py --prepare-data")
        return 1

    try:
        print("=" * 60)
        print("MODULUS ML PIPELINE - FORWARD DIRECTION CLASSIFICATION")
        print("=" * 60)
        print(f"\nConfiguration: {config_path}")
        print(f"Data: {data_file}")

        # Load configuration as dictionary (we need raw dict for custom preprocessing)
        import yaml

        with open(config_path, "r") as f:
            config_dict = yaml.safe_load(f)

        # Build pipeline with custom preprocessing
        pipeline_runner = build_pipeline_with_custom_preprocessing(config_dict)

        # Create PipelineConfig
        pipeline_config = PipelineConfig(
            data_config=config_dict.get("Data", {}),
            preprocessing_config=config_dict.get("Preprocessing", {}),
            model_specs=[
                ModelSpec(name=m["name"], params=m.get("params", {}))
                for m in config_dict.get("Models", [])
            ],
            output_config=config_dict.get("Output", {}),
        )

        # Execute pipeline
        print("\n" + "=" * 60)
        print("STARTING PIPELINE EXECUTION")
        print("=" * 60)

        pipeline_runner.execute(pipeline_config)

        print("\n" + "=" * 60)
        print("✓ PIPELINE COMPLETED SUCCESSFULLY")
        print("=" * 60)

        output_dir = config_dict.get("Output", {}).get("path", "results/")
        print(f"\nResults saved to: {output_dir}")
        print("\nGenerated files:")
        print(f"  - {output_dir}results.csv")
        print(f"  - {output_dir}results.json")
        print(f"  - {output_dir}results.html")
        print(f"  - {output_dir}summary.txt")

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
