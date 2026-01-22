#!/bin/bash
# Build and install emotiv-rs wheel into the poetry environment
#
# Usage:
#   ./build_emotiv.sh              # Build and install
#   ./build_emotiv.sh --check      # Check if installed
#   ./build_emotiv.sh --build-only # Build only, don't install

set -e

cd "$(dirname "$0")"

# Run inside poetry environment
poetry run python scripts/build_emotiv.py "$@"
