# Quick Start Guide

This guide will help you get started with the Modulus ML Pipeline in under 5 minutes.

## Prerequisites

- Python 3.9 or higher
- pip package manager

## Method 1: Automated Quick Start (Recommended)

Run the automated setup script:

```bash
bash scripts/quick_start.sh
```

This will:
1. Create a virtual environment
2. Install all dependencies
3. Generate sample data
4. Create a default configuration
5. Run the pipeline
6. Generate results

## Method 2: Manual Setup

### Step 1: Install Dependencies

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install -r requirements.txt
pip install -e .
```

### Step 2: Generate Sample Data

```bash
python scripts/generate_sample_data.py --output-dir data/
```

This creates sample `.npy` files in the `data/` directory with:
- 300 total samples (3 files × 100 samples)
- 20 features
- Binary classification labels
- Metadata (sample IDs, batch numbers, quality scores)

### Step 3: Create Configuration

```bash
python -m modulus.cli --generate-config
```

This creates a `config.yaml` file with default settings. You can edit it to customize:
- Data source and split ratios
- Preprocessing steps (scaling, PCA)
- Models and their hyperparameters
- Output formats and location

### Step 4: Run the Pipeline

```bash
python -m modulus.cli --config config.yaml
```

### Step 5: View Results

Results are saved in the `results/` directory:
- **results.csv**: Tabular metrics for all models
- **results.json**: JSON-formatted results
- **results.html**: Interactive HTML report (open in browser)
- **summary.txt**: Text summary with best model

**Note**: When running preprocessing experiments (`run_preprocessing_experiments.py`), results are saved to `results/experiments_{mode}_{timestamp}/` and trained models are saved to `models/` folder. See `docs/modulus/EXPERIMENT_FEATURES.md` for details.

## Using Your Own Data

### Data Format

The pipeline expects `.npy` files containing dictionaries with:

```python
{
    "features": np.ndarray,  # Shape: (n_samples, n_features)
    "labels": np.ndarray,    # Shape: (n_samples,)
    "metadata": pd.DataFrame # Optional metadata
}
```

### Creating Your Data Files

```python
import numpy as np
import pandas as pd

# Prepare your data
X = your_features  # numpy array
y = your_labels    # numpy array
metadata = pd.DataFrame({
    "sample_id": range(len(X)),
    # ... other metadata columns
})

# Save to .npy format
data = {
    "features": X,
    "labels": y,
    "metadata": metadata,
}
np.save("data/my_data.npy", data)
```

### Update Configuration

Edit `config.yaml` to point to your data:

```yaml
Data:
  source: "path/to/your/data/"  # Directory containing .npy files
  feature_key: "features"        # Key for features in .npy dict
  target_key: "labels"           # Key for labels in .npy dict
  use_metadata: false            # Include metadata as features?
```

## Customizing Models

### Add Models to Configuration

```yaml
Models:
  - name: LogisticRegression
    params:
      max_iter: 1000
      C: 1.0
      
  - name: RandomForest
    params:
      n_estimators: 200
      max_depth: 10
      
  - name: GradientBoosting
    params:
      n_estimators: 100
      learning_rate: 0.1
      
  - name: SVC
    params:
      kernel: rbf
      C: 1.0
```

### Available Models

- `LogisticRegression`
- `RandomForest` / `RandomForestClassifier`
- `GradientBoosting` / `GradientBoostingClassifier`
- `SVC` / `SVM`
- `DecisionTree` / `DecisionTreeClassifier`
- `NaiveBayes` / `GaussianNB`
- `KNN` / `KNeighborsClassifier`

## Customizing Preprocessing

```yaml
Preprocessing:
  standard_scaler: true      # Standardize features (mean=0, std=1)
  pca_components: 10         # Reduce to 10 dimensions
  # or
  pca_components: 0.95       # Keep 95% of variance
  # or
  pca_components: null       # No PCA
```

## Running Tests

```bash
# Run all tests
pytest

# Run specific test suites
pytest tests/unit/          # Unit tests only
pytest tests/integration/   # Integration tests
pytest tests/e2e/          # End-to-end tests

# Generate coverage report
pytest --cov=modulus --cov-report=html
```

## Using the Makefile

```bash
make help            # Show all available commands
make install         # Install dependencies
make generate-data   # Generate sample data
make generate-config # Generate config file
make run            # Run pipeline
make test           # Run all tests
make coverage       # Run tests with coverage
make clean          # Clean generated files
```

## Troubleshooting

### Issue: No .npy files found

**Solution**: Ensure your data directory contains `.npy` files with the correct structure.

```bash
python scripts/generate_sample_data.py --output-dir data/
```

### Issue: Model not found

**Solution**: Check that the model name in `config.yaml` matches an available model (see list above).

### Issue: Memory error with large datasets

**Solution**: 
- Reduce PCA components to lower dimensionality
- Process data in smaller batches
- Use simpler models (LogisticRegression instead of RandomForest)

## Next Steps

1. **Read the Architecture**: See `SDD.md` for system design details
2. **Explore Examples**: Check `config/` for example configurations
3. **Run Tests**: Verify everything works with `make test`
4. **Customize**: Modify configuration for your specific use case
5. **Extend**: Add custom models, preprocessing, or data loaders

## Getting Help

- Check the full documentation in `README.md`
- Review the SDD in `SDD.md`
- Examine test files for usage examples
- Open an issue on the project repository

## Example Workflow

```bash
# 1. Setup
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Generate sample data
python scripts/generate_sample_data.py

# 3. Create config
python -m modulus.cli --generate-config

# 4. Edit config (optional)
nano config.yaml

# 5. Run pipeline
python -m modulus.cli --config config.yaml

# 6. View results
open results/results.html  # macOS
xdg-open results/results.html  # Linux
start results/results.html  # Windows
```

That's it! You're now ready to use the Modulus ML Pipeline. 🚀

