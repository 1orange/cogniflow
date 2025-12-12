#!/bin/bash
# Quick start script for the Modulus ML Pipeline

set -e

echo "========================================"
echo "Modulus ML Pipeline - Quick Start"
echo "========================================"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Generate sample data
echo ""
echo "Generating sample data..."
python scripts/generate_sample_data.py --output-dir data/

# Generate default configuration
echo ""
echo "Generating default configuration..."
python -m modulus.cli --generate-config --output config.yaml

# Run the pipeline
echo ""
echo "Running the ML pipeline..."
echo "========================================"
python -m modulus.cli --config config.yaml

echo ""
echo "========================================"
echo "Pipeline execution completed!"
echo ""
echo "Results are available in: results/"
echo "  - results.csv"
echo "  - results.json"
echo "  - results.html (open in browser)"
echo "  - summary.txt"
echo "========================================"

