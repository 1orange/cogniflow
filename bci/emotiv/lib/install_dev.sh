#!/bin/bash
# Install emotiv-rs in development mode (editable install)

set -e

cd "$(dirname "$0")"

echo "Installing emotiv-rs in development mode..."
maturin develop --release

echo ""
echo "✓ emotiv-rs installed successfully!"
echo "  You can now import it in Python: 'import emotiv_rs'"

