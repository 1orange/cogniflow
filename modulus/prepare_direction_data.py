#!/usr/bin/env python3
"""
Prepare forward direction data for the modulus pipeline.
Converts raw .npy array into the expected dictionary format with features and labels.
"""

import numpy as np
import pandas as pd
from pathlib import Path


def prepare_forward_data(
    input_file: str = "data/recorded_data_forward_20251110_130851.npy",
    output_file: str = "data/prepared/forward_prepared.npy",
    flatten: bool = True,
):
    """
    Prepare forward direction data for classification.

    Args:
        input_file: Path to raw forward .npy file
        output_file: Path to save prepared data
        flatten: If True, flatten (timesteps, channels) to single feature vector
    """
    print("=" * 60)
    print("PREPARING FORWARD DATA FOR MODULUS PIPELINE")
    print("=" * 60)

    # Load raw data
    print(f"\n1. Loading data from {input_file}...")
    data = np.load(input_file)
    print(f"   Shape: {data.shape}")
    print(f"   Dtype: {data.dtype}")

    # Data shape is (n_windows, timesteps, channels)
    n_windows, n_timesteps, n_channels = data.shape

    # Prepare features
    if flatten:
        print("\n2. Flattening data (timesteps × channels)...")
        # Flatten each window to (n_windows, timesteps * channels)
        features = data.reshape(n_windows, n_timesteps * n_channels)
        print(f"   Flattened shape: {features.shape}")
    else:
        features = data

    # Create binary labels (1 = forward, 0 = not forward)
    # Since we only have forward data, all labels are 1
    print("\n3. Creating labels...")
    labels = np.ones(n_windows, dtype=int)
    print(f"   Labels shape: {labels.shape}")
    print("   All samples labeled as class 1 (forward)")

    # Create metadata
    print("\n4. Creating metadata...")
    metadata = pd.DataFrame(
        {
            "sample_id": range(n_windows),
            "direction": ["forward"] * n_windows,
            "window_index": range(n_windows),
            "n_timesteps": [n_timesteps] * n_windows,
            "n_channels": [n_channels] * n_windows,
        }
    )

    # Package data in modulus format
    prepared_data = {
        "features": features,
        "labels": labels,
        "metadata": metadata,
    }

    # Save prepared data
    print(f"\n5. Saving prepared data to {output_file}...")
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(output_path, prepared_data)

    print("\n✓ Data preparation complete!")
    print("\nDataset summary:")
    print(f"  - Samples: {n_windows}")
    print(f"  - Features: {features.shape[1]}")
    print(f"  - Classes: {len(np.unique(labels))} (all 'forward')")
    print(f"  - Output: {output_file}")

    return prepared_data


def prepare_all_directions_multiclass(
    data_dir: str = "data",
    output_file: str = "data/prepared/directions_multiclass.npy",
    flatten: bool = True,
):
    """
    Prepare all direction data for multi-class classification.

    Args:
        data_dir: Directory containing raw direction .npy files
        output_file: Path to save prepared data
        flatten: If True, flatten (timesteps, channels) to single feature vector
    """
    print("=" * 60)
    print("PREPARING MULTI-CLASS DIRECTION DATA")
    print("=" * 60)

    data_dir = Path(data_dir)
    directions = ["backward", "forward", "left", "right"]

    all_features = []
    all_labels = []
    all_metadata = []

    for label_idx, direction in enumerate(directions):
        # Find file for this direction
        pattern = f"recorded_data_{direction}_*.npy"
        files = list(data_dir.glob(pattern))

        if not files:
            print(f"Warning: No files found for direction '{direction}'")
            continue

        file_path = files[0]
        print(f"\n{label_idx + 1}. Loading {direction} from {file_path.name}...")

        # Load data
        data = np.load(file_path)
        n_windows, n_timesteps, n_channels = data.shape
        print(f"   Shape: {data.shape}")

        # Flatten if requested
        if flatten:
            features = data.reshape(n_windows, n_timesteps * n_channels)
        else:
            features = data

        # Create labels
        labels = np.full(n_windows, label_idx, dtype=int)

        # Create metadata
        metadata = pd.DataFrame(
            {
                "sample_id": range(
                    len(all_features) * 1000, (len(all_features) + 1) * 1000
                )[:n_windows],
                "direction": [direction] * n_windows,
                "direction_label": [label_idx] * n_windows,
                "window_index": range(n_windows),
            }
        )

        all_features.append(features)
        all_labels.append(labels)
        all_metadata.append(metadata)

        print(f"   Added {n_windows} samples for class {label_idx} ({direction})")

    # Combine all data
    print("\nCombining all directions...")
    features = np.vstack(all_features)
    labels = np.hstack(all_labels)
    metadata = pd.concat(all_metadata, ignore_index=True)

    # Package data
    prepared_data = {
        "features": features,
        "labels": labels,
        "metadata": metadata,
    }

    # Save
    print(f"\nSaving to {output_file}...")
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(output_path, prepared_data)

    print("\n✓ Multi-class data preparation complete!")
    print("\nDataset summary:")
    print(f"  - Total samples: {len(features)}")
    print(f"  - Features per sample: {features.shape[1]}")
    print(f"  - Number of classes: {len(directions)}")
    print("  - Class distribution:")
    for idx, direction in enumerate(directions):
        count = np.sum(labels == idx)
        print(
            f"      {idx} ({direction}): {count} samples ({count / len(labels) * 100:.1f}%)"
        )
    print(f"  - Output: {output_file}")

    return prepared_data


def prepare_binary_forward_vs_rest(
    data_dir: str = "data",
    output_file: str = "data/prepared/forward_vs_rest_binary.npy",
    flatten: bool = True,
):
    """
    Prepare binary classification: forward vs not-forward (rest).

    This creates a binary classification dataset where:
    - Class 1: forward direction
    - Class 0: not-forward (backward, left, right combined)

    Args:
        data_dir: Directory containing raw direction .npy files
        output_file: Path to save prepared data
        flatten: If True, flatten (timesteps, channels) to single feature vector
    """
    print("=" * 60)
    print("PREPARING BINARY: FORWARD vs NOT-FORWARD")
    print("=" * 60)

    data_dir = Path(data_dir)
    directions = ["backward", "forward", "left", "right"]

    all_features = []
    all_labels = []
    all_metadata = []

    for direction in directions:
        # Find file for this direction
        pattern = f"recorded_data_{direction}_*.npy"
        files = list(data_dir.glob(pattern))

        if not files:
            print(f"Warning: No files found for direction '{direction}'")
            continue

        file_path = files[0]
        print(f"\n{direction.upper()}:")

        # Load data
        data = np.load(file_path)
        n_windows, n_timesteps, n_channels = data.shape
        print(f"  Loading from {file_path.name}")
        print(f"  Shape: {data.shape}")

        # Flatten if requested
        if flatten:
            features = data.reshape(n_windows, n_timesteps * n_channels)
        else:
            features = data

        # Create binary labels: 1 for forward, 0 for everything else
        if direction == "forward":
            labels = np.ones(n_windows, dtype=int)
            label_name = "forward"
        else:
            labels = np.zeros(n_windows, dtype=int)
            label_name = "not-forward"

        # Create metadata
        metadata = pd.DataFrame(
            {
                "sample_id": range(
                    len(all_features) * 1000, (len(all_features) + 1) * 1000
                )[:n_windows],
                "original_direction": [direction] * n_windows,
                "binary_label": [label_name] * n_windows,
                "window_index": range(n_windows),
            }
        )

        all_features.append(features)
        all_labels.append(labels)
        all_metadata.append(metadata)

        print(
            f"  Added {n_windows} samples as class '{label_name}' (label={labels[0]})"
        )

    # Combine all data
    print("\nCombining all directions...")
    features = np.vstack(all_features)
    labels = np.hstack(all_labels)
    metadata = pd.concat(all_metadata, ignore_index=True)

    # Package data
    prepared_data = {
        "features": features,
        "labels": labels,
        "metadata": metadata,
    }

    # Save
    print(f"\nSaving to {output_file}...")
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(output_path, prepared_data)

    print("\n✓ Binary classification data preparation complete!")
    print("\nDataset summary:")
    print(f"  - Total samples: {len(features)}")
    print(f"  - Features per sample: {features.shape[1]}")
    print("  - Number of classes: 2 (binary)")
    print("  - Class distribution:")

    forward_count = np.sum(labels == 1)
    not_forward_count = np.sum(labels == 0)
    print(
        f"      1 (forward):     {forward_count} samples ({forward_count / len(labels) * 100:.1f}%)"
    )
    print(
        f"      0 (not-forward): {not_forward_count} samples ({not_forward_count / len(labels) * 100:.1f}%)"
    )
    print(f"  - Class imbalance ratio: 1:{not_forward_count / forward_count:.2f}")
    print(f"  - Output: {output_file}")

    return prepared_data


def main():
    """Main execution function."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Prepare direction data for modulus pipeline"
    )
    parser.add_argument(
        "--mode",
        choices=["forward-only", "multiclass", "binary"],
        default="forward-only",
        help="Preparation mode: forward-only, multiclass, or binary (forward vs rest)",
    )
    parser.add_argument(
        "--data-dir", default="data", help="Directory containing raw .npy files"
    )
    parser.add_argument(
        "--output", help="Output file path (optional, uses default based on mode)"
    )
    parser.add_argument(
        "--no-flatten",
        action="store_true",
        help="Keep 3D structure instead of flattening",
    )

    args = parser.parse_args()

    flatten = not args.no_flatten

    if args.mode == "forward-only":
        output = args.output or "data/prepared/forward_prepared.npy"
        prepare_forward_data(
            input_file=f"{args.data_dir}/recorded_data_forward_20251110_130851.npy",
            output_file=output,
            flatten=flatten,
        )
    elif args.mode == "multiclass":
        output = args.output or "data/prepared/directions_multiclass.npy"
        prepare_all_directions_multiclass(
            data_dir=args.data_dir, output_file=output, flatten=flatten
        )
    else:  # binary
        output = args.output or "data/prepared/forward_vs_rest_binary.npy"
        prepare_binary_forward_vs_rest(
            data_dir=args.data_dir, output_file=output, flatten=flatten
        )


if __name__ == "__main__":
    main()
