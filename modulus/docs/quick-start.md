# Quick Start Guide

Get started with the Modulus ML Pipeline in 5 minutes.

## Prerequisites

- Python 3.13 (or 3.9+)
- Poetry package manager
- Your EEG direction data in `.npy` format

## Step 1: Install Dependencies

```bash
cd /path/to/modulus
poetry install
```

## Step 2: Prepare Your Data

Choose a preparation mode:

### Option A: Multiclass (Recommended)

For standard direction classification with all 4 directions:

```bash
poetry run python prepare_direction_data.py --mode multiclass
```

Creates: `data/directions_multiclass.npy` with 2814 samples across 4 classes.

### Option B: Forward-Only

For single-direction analysis:

```bash
poetry run python prepare_direction_data.py --mode forward-only
```

Creates: `data/forward_prepared.npy` with 690 forward samples.

**💡 See [Preprocessing Modes](preprocessing-modes.md) for detailed comparison.**

## Step 3: Run the Pipeline

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

## Step 4: View Results

Results are saved in `results/forward_direction/`:

```bash
# View HTML report (interactive)
xdg-open results/forward_direction/results.html

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
# Edit the config file
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

## Next Steps

- **[Add Custom Preprocessing](adding-custom-preprocessing.md)** - Create your own preprocessing techniques
- **[Preprocessing Modes](preprocessing-modes.md)** - Understand forward-only vs multiclass
- **[Configuration Guide](../config/forward_direction_config.yaml)** - See all configuration options
- **[Architecture](../SDD.md)** - Understand the system design

## Troubleshooting

### Issue: ModuleNotFoundError

```bash
# Make sure you're using poetry
poetry run python run_forward_pipeline.py

# Or activate the virtual environment
poetry shell
python run_forward_pipeline.py
```

### Issue: Data file not found

```bash
# Prepare the data first
poetry run python prepare_direction_data.py --mode multiclass
```

### Issue: Out of memory

```yaml
# In config file, reduce dimensionality:
Preprocessing:
  downsample_factor: 2  # Reduce time resolution
  pca_components: 30    # Fewer PCA components
```

## Complete Example Workflow

```bash
# 1. Navigate to project
cd /home/jean/dev/diplomka/modulus

# 2. Install dependencies
poetry install

# 3. Prepare data
poetry run python prepare_direction_data.py --mode multiclass

# 4. Run pipeline
poetry run python run_forward_pipeline.py

# 5. View results
xdg-open results/forward_direction/results.html

# 6. Try custom preprocessing
nano config/forward_direction_config.yaml
# ... edit preprocessing section ...

# 7. Run again with changes
poetry run python run_forward_pipeline.py

# 8. Compare results
diff results/forward_direction/results_*.csv
```

That's it! You're now using the Modulus ML Pipeline. 🚀

