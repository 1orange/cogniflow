# Modulus ML Pipeline — Quick Start

> **Part of Cogniflow** — This guide covers the integrated ML pipeline module.

Get started with the Modulus ML Pipeline in 5 minutes.

## Prerequisites

- **Cogniflow installed** via Poetry (see [main README](../../README.md))
- Python 3.11+ (as per main project requirements)
- EEG data in `.npy` format (recorded via Cogniflow or your own data)

## Method 1: Using Pygame Interface (Recommended)

The easiest way to use Modulus is through Cogniflow's built-in UI:

```bash
# From cogniflow root directory
poetry run python main.py
```

1. Press `[M]` to enter **ML Pipeline (Modulus)**
2. Use `[UP]/[DOWN]` to select experiment mode:
   - **Binary** — Forward vs not-forward classification
   - **Multiclass** — All 4 directions classification
   - **Both** — Run both experiments
3. Toggle options:
   - `[Q]` — Quick Mode (faster, fewer iterations)
   - `[H]` — Hyperparameter Tuning (GridSearchCV)
4. Press `[ENTER]` to run experiments
5. Results appear in:
   - `results/experiments_{mode}_{timestamp}/`
   - `models/` (trained model files)

## Method 2: Using CLI

Run the pipeline from the command line:

```bash
# From cogniflow root directory
cd modulus

# Prepare your data first
poetry run python prepare_direction_data.py --mode multiclass

# Run the pipeline
poetry run python run_forward_pipeline.py
```

Or use the CLI interface directly:

```bash
poetry run python -m modulus.cli --config config/forward_direction_config.yaml
```

## Data Preparation

### Option A: Use Cogniflow Record Scene

1. Launch Cogniflow: `poetry run python main.py`
2. Press `[R]` for Record scene
3. Follow the wizard to record EEG data
4. Data saved to `data/recorded_data_<direction>_<timestamp>.npy`

### Option B: Prepare Existing Data

If you already have recorded data:

```bash
cd modulus

# For multiclass (4 directions) - Recommended
poetry run python prepare_direction_data.py --mode multiclass

# For binary (forward vs rest)
poetry run python prepare_direction_data.py --mode binary
```

## Viewing Results

Results are saved in multiple formats:

```bash
# HTML report (interactive)
xdg-open modulus/results/forward_direction/results.html   # Linux
open modulus/results/forward_direction/results.html       # macOS
start modulus/results/forward_direction/results.html      # Windows

# CSV for analysis
cat modulus/results/forward_direction/results.csv

# Summary
cat modulus/results/forward_direction/summary.txt
```

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

## Configuration

Edit `modulus/config/forward_direction_config.yaml`:

```yaml
Preprocessing:
  standard_scaler: true
  pca_components: 100
  
  # Optional: feature extraction
  extract_features: true
  feature_list:
    - mean
    - std
    - energy

Models:
  - name: LogisticRegression
  - name: RandomForest
  - name: SVM
  - name: GradientBoosting
```

## Troubleshooting

### ModuleNotFoundError

```bash
# Ensure you're running from cogniflow root with poetry
poetry run python main.py
```

### Data file not found

```bash
# Prepare data first
cd modulus
poetry run python prepare_direction_data.py --mode multiclass
```

### Out of memory

Reduce dimensionality in config:

```yaml
Preprocessing:
  downsample_factor: 2
  pca_components: 30
```

## Next Steps

- **[Experiment Features](EXPERIMENT_FEATURES.md)** — Advanced experiment configuration
- **[Preprocessing Modes](../../modulus/docs/preprocessing-modes.md)** — Forward-only vs multiclass
- **[Custom Preprocessing](../../modulus/docs/custom-preprocessing.md)** — Add your own techniques
- **[Architecture](../../modulus/docs/ARCHITECTURE.md)** — System design

## See Also

- [Main Cogniflow README](../../README.md)
- [Modulus Documentation Index](../../modulus/docs/INDEX.md)
- [System Design Document](../../modulus/SDD.md)
