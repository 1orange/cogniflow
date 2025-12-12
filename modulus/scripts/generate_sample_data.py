#!/usr/bin/env python3
"""Generate sample .npy data files for testing the pipeline."""

import numpy as np
import pandas as pd
from pathlib import Path
import argparse


def generate_sample_data(
    output_dir: str = "data/",
    n_files: int = 3,
    samples_per_file: int = 100,
    n_features: int = 20,
    n_classes: int = 2,
    random_state: int = 42,
):
    """
    Generate sample .npy files with embedded metadata.

    Args:
        output_dir: Directory to save .npy files
        n_files: Number of .npy files to generate
        samples_per_file: Number of samples per file
        n_features: Number of features
        n_classes: Number of classes for classification
        random_state: Random seed for reproducibility
    """
    np.random.seed(random_state)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Generating {n_files} sample .npy files...")
    print(f"Output directory: {output_path.absolute()}")

    for i in range(n_files):
        # Generate synthetic classification data
        X = np.random.randn(samples_per_file, n_features)

        # Add some signal to make it learnable
        # Features 0-2 are informative
        y = (X[:, 0] + X[:, 1] - X[:, 2] > 0).astype(int)

        # Add some noise
        noise_idx = np.random.choice(
            samples_per_file, size=int(0.1 * samples_per_file), replace=False
        )
        y[noise_idx] = 1 - y[noise_idx]

        # Generate metadata
        metadata = pd.DataFrame(
            {
                "sample_id": range(i * samples_per_file, (i + 1) * samples_per_file),
                "batch": [i] * samples_per_file,
                "quality_score": np.random.uniform(0.5, 1.0, samples_per_file),
                "category": np.random.choice(["A", "B", "C"], samples_per_file),
            }
        )

        # Create data dictionary
        data = {
            "features": X,
            "labels": y,
            "metadata": metadata,
        }

        # Save to .npy file
        file_path = output_path / f"sample_batch_{i}.npy"
        np.save(file_path, data)
        print(f"  Created: {file_path.name} ({samples_per_file} samples)")

    print(f"\nTotal samples: {n_files * samples_per_file}")
    print(f"Feature dimensions: {n_features}")
    print(f"Number of classes: {n_classes}")
    print("\nYou can now run the pipeline with:")
    print("  python -m modulus.cli --config config.yaml")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate sample .npy data for testing the ML pipeline"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/",
        help="Output directory for .npy files (default: data/)",
    )
    parser.add_argument(
        "--n-files",
        type=int,
        default=3,
        help="Number of .npy files to generate (default: 3)",
    )
    parser.add_argument(
        "--samples-per-file",
        type=int,
        default=100,
        help="Number of samples per file (default: 100)",
    )
    parser.add_argument(
        "--n-features",
        type=int,
        default=20,
        help="Number of features (default: 20)",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Random seed (default: 42)",
    )

    args = parser.parse_args()

    generate_sample_data(
        output_dir=args.output_dir,
        n_files=args.n_files,
        samples_per_file=args.samples_per_file,
        n_features=args.n_features,
        random_state=args.random_state,
    )


if __name__ == "__main__":
    main()
