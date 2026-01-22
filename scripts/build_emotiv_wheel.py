#!/usr/bin/env python3
"""
Build and install emotiv-rs wheel for Poetry.

This script:
1. Cleans old wheels
2. Builds a fresh wheel using maturin
3. Installs it into the Poetry environment using pip

Usage:
    python scripts/build_emotiv_wheel.py

Or make it executable and run directly:
    chmod +x scripts/build_emotiv_wheel.py
    ./scripts/build_emotiv_wheel.py
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, cwd=None, check=True):
    """Run a shell command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr and result.returncode != 0:
        print(result.stderr, file=sys.stderr)
    return result


def main():
    """Build and install the emotiv-rs wheel."""
    # Get the project root
    project_root = Path(__file__).parent.parent
    lib_dir = project_root / "bci" / "emotiv" / "lib"

    if not lib_dir.exists():
        print(f"Error: Library directory not found at {lib_dir}")
        sys.exit(1)

    print("=" * 70)
    print("Building and Installing emotiv-rs Wheel")
    print("=" * 70)
    print()

    # Step 1: Clean old wheels
    wheels_dir = lib_dir / "wheels"
    if wheels_dir.exists():
        print("Cleaning old wheels...")
        for wheel_file in wheels_dir.glob("*.whl"):
            print(f"  Removing {wheel_file.name}")
            wheel_file.unlink()

    # Step 2: Build the wheel using maturin
    print("\nBuilding wheel with maturin...")
    print("This may take a few minutes...")
    try:
        # Use poetry run to ensure we use the correct maturin version
        # Use --universal flag to ensure compatibility
        result = run_command(
            [
                "poetry",
                "run",
                "maturin",
                "build",
                "--release",
                "--out",
                "wheels",
                "--compatibility",
                "linux",
            ],
            cwd=lib_dir,
            check=True,
        )
        print("✓ Wheel built successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error building wheel: {e}")
        print("\nTrying without compatibility flag...")
        try:
            result = run_command(
                ["poetry", "run", "maturin", "build", "--release", "--out", "wheels"],
                cwd=lib_dir,
                check=True,
            )
            print("✓ Wheel built successfully")
        except subprocess.CalledProcessError as e2:
            print(f"Error building wheel: {e2}")
            sys.exit(1)

    # Step 3: Find the built wheel
    wheel_files = list(wheels_dir.glob("*.whl"))
    if not wheel_files:
        print("Error: No wheel file found after building")
        sys.exit(1)

    wheel_file = wheel_files[0]
    print(f"\nFound wheel: {wheel_file.name}")

    # Step 4: Install the wheel using Poetry
    print("\nInstalling wheel into Poetry environment...")
    wheel_path = wheel_file.resolve()

    # Try using poetry add first (preferred method)
    print("Installing with Poetry...")
    try:
        # Use relative path for portability
        wheel_relative = wheel_file.relative_to(project_root)

        # Use poetry add with the relative wheel path
        # Poetry will handle the installation and update pyproject.toml if needed
        result = run_command(
            ["poetry", "add", str(wheel_relative)], cwd=project_root, check=True
        )
        print("✓ Wheel installed successfully using Poetry")

        # Convert absolute path to relative path in pyproject.toml for portability
        pyproject_path = project_root / "pyproject.toml"
        if pyproject_path.exists():
            import re

            content = pyproject_path.read_text()
            # Replace absolute file:// path with relative path
            # Pattern: file:///absolute/path/to/wheel.whl
            absolute_pattern = (
                r"file://" + re.escape(str(project_root.resolve())) + r'/([^"]+\.whl)'
            )
            relative_replacement = r"file:///${PROJECT_ROOT}/\1"
            new_content = re.sub(absolute_pattern, relative_replacement, content)

            if new_content != content:
                pyproject_path.write_text(new_content)
                print("✓ Updated pyproject.toml to use relative path")
    except subprocess.CalledProcessError as e:
        print(f"Poetry add failed: {e}")
        print("\nFalling back to pip installation in Poetry environment...")
        try:
            # First, try to uninstall any existing version
            print("Removing any existing installation...")
            run_command(
                ["poetry", "run", "pip", "uninstall", "-y", "emotiv-rs"],
                cwd=project_root,
                check=False,  # Don't fail if not installed
            )

            # Install the wheel using pip in poetry environment
            # Use --no-deps since we're managing dependencies via poetry
            result = run_command(
                [
                    "poetry",
                    "run",
                    "pip",
                    "install",
                    str(wheel_path),
                    "--force-reinstall",
                    "--no-deps",
                ],
                cwd=project_root,
                check=True,
            )
            print("✓ Wheel installed successfully using pip")
            print(
                "\nNote: Wheel installed via pip. Consider using 'poetry add' manually:"
            )
            print(f"  poetry add {wheel_path}")
        except subprocess.CalledProcessError as e2:
            print(f"Error installing wheel: {e2}")
            print("\nYou can manually install the wheel with:")
            print(f"  poetry add {wheel_path}")
            print("  or")
            print(f"  poetry run pip install {wheel_path}")
            sys.exit(1)

    print("\n" + "=" * 70)
    print("✓ emotiv-rs wheel built and installed successfully!")
    print("=" * 70)
    print(f"\nWheel location: {wheel_path}")
    print("\nYou can now import it in Python:")
    print("  import emotiv_rs")
    print("\nTo verify installation:")
    print("  poetry run python -c 'import emotiv_rs; print(emotiv_rs.__file__)'")


if __name__ == "__main__":
    main()
