#!/bin/bash
# Build the emotiv-rs wheel

set -e

cd "$(dirname "$0")"

# Build the wheel
maturin build --release --out wheels

echo "Wheel built successfully in wheels/"
ls -lh wheels/

