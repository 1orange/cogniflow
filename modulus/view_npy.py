#!/usr/bin/env python3
"""
Script to view and inspect NumPy .npy files
"""

import numpy as np
import argparse
import sys


def format_array_preview(arr, max_items=10):
    """Format array for preview, truncating if too large"""
    if arr.size == 0:
        return "[]"

    # For 1D arrays
    if arr.ndim == 1:
        if len(arr) <= max_items:
            return str(arr)
        else:
            preview = np.concatenate([arr[: max_items // 2], arr[-(max_items // 2) :]])
            return f"[{arr[0]} {arr[1]} ... {arr[-2]} {arr[-1]}]"

    # For multidimensional arrays, use numpy's smart printing
    with np.printoptions(threshold=max_items, edgeitems=3, linewidth=100):
        return str(arr)


def view_npy(file_path, show_stats=False, show_full=False):
    """View contents of a .npy file"""
    try:
        # Load the array
        arr = np.load(file_path)

        print(f"\n{'=' * 60}")
        print(f"File: {file_path}")
        print(f"{'=' * 60}")

        # Basic info
        print(f"\nShape:     {arr.shape}")
        print(f"Dtype:     {arr.dtype}")
        print(f"Size:      {arr.size} elements")
        print(f"Dimensions: {arr.ndim}")

        if arr.size > 0:
            print(f"Memory:    {arr.nbytes / 1024:.2f} KB")

        # Statistics for numeric arrays
        if show_stats and np.issubdtype(arr.dtype, np.number):
            print("\nStatistics:")
            print(f"  Min:     {np.min(arr)}")
            print(f"  Max:     {np.max(arr)}")
            print(f"  Mean:    {np.mean(arr):.6f}")
            print(f"  Std:     {np.std(arr):.6f}")
            print(f"  Median:  {np.median(arr):.6f}")

        # Show array contents
        print("\nData:")
        if show_full:
            print(arr)
        else:
            print(format_array_preview(arr, max_items=20))

        print(f"\n{'=' * 60}\n")

        return True

    except FileNotFoundError:
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error loading file: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="View and inspect NumPy .npy files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s data.npy                    # View basic info and preview
  %(prog)s data.npy --stats            # Include statistics
  %(prog)s data.npy --full             # Show full array contents
  %(prog)s file1.npy file2.npy         # View multiple files
        """,
    )

    parser.add_argument("files", nargs="+", help="Path(s) to .npy file(s) to view")

    parser.add_argument(
        "-s",
        "--stats",
        action="store_true",
        help="Show statistical information (min, max, mean, std, median)",
    )

    parser.add_argument(
        "-f",
        "--full",
        action="store_true",
        help="Show full array contents (use with caution for large arrays)",
    )

    args = parser.parse_args()

    # Process each file
    success = True
    for file_path in args.files:
        if not view_npy(file_path, show_stats=args.stats, show_full=args.full):
            success = False

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
