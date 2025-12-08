"""Command-line interface for the pipeline."""

import argparse
import sys
from pathlib import Path

from modulus.config import ConfigLoader
from modulus.container import DependencyContainer


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Modular Machine Learning Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with configuration file
  python -m modulus.cli --config config.yaml
  
  # Generate default configuration
  python -m modulus.cli --generate-config
        """,
    )

    parser.add_argument(
        "--config",
        type=str,
        help="Path to YAML configuration file",
    )

    parser.add_argument(
        "--generate-config",
        action="store_true",
        help="Generate a default configuration file",
    )

    parser.add_argument(
        "--output",
        type=str,
        default="config.yaml",
        help="Output path for generated configuration (default: config.yaml)",
    )

    args = parser.parse_args()

    # Handle configuration generation
    if args.generate_config:
        generate_default_config(args.output)
        return 0

    # Require config file for pipeline execution
    if not args.config:
        parser.error("--config is required for pipeline execution")

    # Execute pipeline
    try:
        execute_pipeline(args.config)
        return 0
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


def execute_pipeline(config_path: str) -> None:
    """
    Execute the ML pipeline with given configuration.

    Args:
        config_path: Path to configuration file
    """
    print(f"Loading configuration from: {config_path}")

    # Load configuration
    config = ConfigLoader.load_from_file(config_path)

    # Build pipeline with dependency injection
    pipeline_runner = DependencyContainer.build_pipeline_runner(config)

    # Execute pipeline
    pipeline_runner.execute(config)


def generate_default_config(output_path: str) -> None:
    """
    Generate a default configuration file.

    Args:
        output_path: Path where to save the configuration
    """
    import yaml

    output_file = Path(output_path)

    if output_file.exists():
        response = input(f"{output_path} already exists. Overwrite? (y/n): ")
        if response.lower() != "y":
            print("Aborted.")
            return

    # Get default configuration
    default_config = ConfigLoader.get_default_config()

    # Write to file
    with open(output_file, "w") as f:
        yaml.dump(default_config, f, default_flow_style=False, sort_keys=False)

    print(f"Default configuration generated: {output_path}")
    print("\nYou can now edit this file and run:")
    print(f"  python -m modulus.cli --config {output_path}")


if __name__ == "__main__":
    sys.exit(main())
