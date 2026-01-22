#!/usr/bin/env python3
"""
Build and install the emotiv-rs wheel into the poetry environment.

Usage:
    python scripts/build_emotiv.py           # Build and install
    python scripts/build_emotiv.py --check   # Check if emotiv-rs is installed
    python scripts/build_emotiv.py --build-only  # Build wheel without installing
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
EMOTIV_LIB_DIR = PROJECT_ROOT / "bci" / "emotiv" / "lib"
WHEELS_DIR = PROJECT_ROOT / "bci" / "emotiv" / "wheels"


def get_wheel_pattern() -> str:
    """Return a glob pattern for emotiv-rs wheels."""
    return "emotiv_rs-*.whl"


def find_latest_wheel(directory: Path) -> Path | None:
    """Find the most recent emotiv-rs wheel in a directory."""
    wheels = list(directory.glob(get_wheel_pattern()))
    if not wheels:
        return None
    # Return the most recently modified wheel
    return max(wheels, key=lambda p: p.stat().st_mtime)


def check_installed() -> bool:
    """Check if emotiv-rs is installed in the current environment."""
    result = subprocess.run(
        ["python", "-c", "import emotiv_rs; print(emotiv_rs.__file__)"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print(f"emotiv-rs is installed: {result.stdout.strip()}")
        return True
    else:
        print("emotiv-rs is NOT installed")
        return False


def build_wheel() -> Path:
    """Build the emotiv-rs wheel using maturin."""
    print("Building emotiv-rs wheel...")
    
    # Create output directory
    WHEELS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Clean old wheels from target directory
    for old_wheel in WHEELS_DIR.glob(get_wheel_pattern()):
        print(f"Removing old wheel: {old_wheel.name}")
        old_wheel.unlink()
    
    # Prepare environment with cargo in PATH
    env = os.environ.copy()
    cargo_bin = Path.home() / ".cargo" / "bin"
    if cargo_bin.exists():
        env["PATH"] = f"{cargo_bin}:{env.get('PATH', '')}"
    
    # Run maturin build, output directly to wheels dir
    result = subprocess.run(
        ["maturin", "build", "--release", "--out", str(WHEELS_DIR)],
        cwd=EMOTIV_LIB_DIR,
        env=env,
    )
    
    if result.returncode != 0:
        print("Error: maturin build failed", file=sys.stderr)
        sys.exit(1)
    
    # Find the built wheel
    wheel = find_latest_wheel(WHEELS_DIR)
    if not wheel:
        print("Error: No wheel found after build", file=sys.stderr)
        sys.exit(1)
    
    print(f"Built: {wheel.name}")
    return wheel


def install_wheel(wheel_path: Path) -> None:
    """Install the wheel into the current Python environment."""
    print(f"Installing {wheel_path.name}...")
    
    # Use pip to install (works whether inside poetry env or not)
    result = subprocess.run(
        ["pip", "install", "--force-reinstall", str(wheel_path)],
    )
    
    if result.returncode != 0:
        print("Error: pip install failed", file=sys.stderr)
        sys.exit(1)
    
    print("Installation complete!")


def main():
    parser = argparse.ArgumentParser(
        description="Build and install emotiv-rs wheel"
    )
    parser.add_argument(
        "--check", 
        action="store_true", 
        help="Only check if emotiv-rs is installed"
    )
    parser.add_argument(
        "--build-only", 
        action="store_true", 
        help="Only build the wheel, don't install"
    )
    args = parser.parse_args()
    
    os.chdir(PROJECT_ROOT)
    
    if args.check:
        sys.exit(0 if check_installed() else 1)
    
    # Build the wheel
    wheel_path = build_wheel()
    
    if args.build_only:
        print(f"\nWheel built at: {wheel_path}")
        print("To install manually: pip install", wheel_path)
        return
    
    # Install the wheel
    install_wheel(wheel_path)
    
    # Verify installation
    print("\nVerifying installation...")
    check_installed()


if __name__ == "__main__":
    main()
