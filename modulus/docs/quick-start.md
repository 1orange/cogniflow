# Quick Start Guide

> **Part of [Cogniflow](../../README.md)** — Get started with the ML pipeline in 5 minutes

## Prerequisites

- **Cogniflow installed** via Poetry (see [main README](../../README.md))
- Python 3.11+
- EEG direction data in `.npy` format (from Cogniflow Record scene or your own data)

## Method 1: Pygame UI (Easiest)

The simplest way to run ML experiments:

```bash
# From cogniflow root
poetry run python main.py
```

1. Press `[M]` to enter **ML Pipeline (Modulus)**
2. Select experiment mode: `[UP]/[DOWN]`
   - Binary — Forward vs not-forward
   - Multiclass — All 4 directions
   - Both — Run both experiments
3. Toggle options:
   - `[Q]` — Quick Mode
   - `[H]` — Hyperparameter Tuning
4. Press `[ENTER]` to run
5. Results saved to `results/` and `models/`

## Method 2: CLI

### Step 1: Prepare Your Data

Choose a preparation mode:

#### Option A: Multiclass (Recommended)

For standard direction classification with all 4 directions:

```bash
cd modulus
poetry run python prepare_direction_data.py --mode multiclass
```

Creates: `data/directions_multiclass.npy` with all direction samples across 4 classes.

#### Option B: Binary

For forward vs rest classification:

```bash
poetry run python prepare_direction_data.py --mode binary
```

Creates: `data/forward_vs_rest_binary.npy` with 2 classes.

#### Option C: Forward-Only

For single-direction analysis:

```bash
poetry run python prepare_direction_data.py --mode forward-only
```

Creates: `data/forward_prepared.npy` with forward samples only.

**💡 See [Preprocessing Modes](preprocessing-modes.md) for detailed comparison.**

### Step 2: Run the Pipeline

```bash
poetry run python run_forward_pipeline.py
```

This will:
1. Load the prepared data
2. Split into train/val/test (70/15/15)
3. Apply preprocessing (scaling + PCA)
4. Train 4 models: Logistic Regression, Decision Tree, SVM, Random Forest
5. Evaluate and compare results
6. Generate reports

### Step 3: View Results

Results are saved in `results/forward_direction/`:

```bash
# View HTML report (interactive)
xdg-open results/forward_direction/results.html   # Linux
open results/forward_direction/results.html       # macOS

# View CSV results
cat results/forward_direction/results.csv

# View summary
cat results/forward_direction/summary.txt
```

## What You'll Get

### Generated Files

- **results.csv**: Tabular comparison of all models
- **results.json**: Machine-readable results
- **results.html**: Interactive visualization
- **summary.txt**: Best model recommendation

### Example Output

```
Model Comparison Results:
┌─────────────────────┬──────────┬───────────┬────────┬──────────┐
│ Model               │ Accuracy │ Precision │ Recall │ F1-Score │
├─────────────────────┼──────────┼───────────┼────────┼──────────┤
│ Random Forest       │ 0.8523   │ 0.8534    │ 0.8523 │ 0.8507   │
│ SVM                 │ 0.8312   │ 0.8289    │ 0.8312 │ 0.8296   │
│ Logistic Regression │ 0.7956   │ 0.7978    │ 0.7956 │ 0.7945   │
│ Decision Tree       │ 0.7234   │ 0.7156    │ 0.7234 │ 0.7189   │
└─────────────────────┴──────────┴───────────┴────────┴──────────┘

Best model: Random Forest (Accuracy: 0.8523)
```

## Customize the Pipeline

### Edit Configuration

```bash
nano config/forward_direction_config.yaml
```

Example customizations:

```yaml
Preprocessing:
  # Add feature extraction
  extract_features: true
  feature_list:
    - mean
    - std
    - energy
  
  # Adjust PCA
  pca_components: 50

Models:
  # Add more models or change parameters
  - name: GradientBoosting
    params:
      n_estimators: 200
      learning_rate: 0.05
```

### Run with Custom Config

```bash
poetry run python run_forward_pipeline.py --config config/my_custom_config.yaml
```

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

## Next Steps

- **[Preprocessing Modes](preprocessing-modes.md)** — Understand forward-only vs multiclass
- **[Add Custom Preprocessing](adding-custom-preprocessing.md)** — Create your own techniques
- **[Custom Preprocessing Guide](custom-preprocessing.md)** — See available options
- **[Architecture (SDD)](../SDD.md)** — Understand the system design
- **[Experiment Features](../../docs/modulus/EXPERIMENT_FEATURES.md)** — Advanced UI experiments

## Troubleshooting

### ModuleNotFoundError

```bash
# Make sure you're using poetry from cogniflow root
poetry run python main.py

# Or for CLI from modulus directory
cd modulus
poetry run python run_forward_pipeline.py
```

### Data file not found

```bash
# Prepare the data first
cd modulus
poetry run python prepare_direction_data.py --mode multiclass
```

### Out of memory

```yaml
# In config file, reduce dimensionality:
Preprocessing:
  downsample_factor: 2  # Reduce time resolution
  pca_components: 30    # Fewer PCA components
```

## Complete Example Workflow

```bash
# 1. Navigate to cogniflow root
cd /path/to/cogniflow

# 2. Record data (optional - use Cogniflow UI)
poetry run python main.py  # Press [R] for Record

# 3. Prepare data
cd modulus
poetry run python prepare_direction_data.py --mode multiclass

# 4. Run pipeline
poetry run python run_forward_pipeline.py

# 5. View results
xdg-open results/forward_direction/results.html

# 6. Try custom preprocessing
nano config/forward_direction_config.yaml

# 7. Run again with changes
poetry run python run_forward_pipeline.py
```

That's it! You're now using the Modulus ML Pipeline. 🚀
