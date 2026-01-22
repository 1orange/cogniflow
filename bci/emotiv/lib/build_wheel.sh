#!/bin/bash
# Build the emotiv-rs wheel

set -e

# Ensure Rust toolchain is on PATH when the script is invoked non-interactively
if [ -f "$HOME/.cargo/env" ]; then
    . "$HOME/.cargo/env"
fi

cd "$(dirname "$0")"

# Build the wheel
maturin build --release --out wheels

echo "Wheel built successfully in wheels/"
ls -lh wheels/

