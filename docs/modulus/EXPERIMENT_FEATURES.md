# Preprocessing Experiment Features

This document describes all features available in the comprehensive preprocessing experiment system.

## Overview

The preprocessing experiment system (`modulus/run_preprocessing_experiments.py`) automatically tests all combinations of preprocessing techniques, models, and data split ratios to find optimal configurations.

## Key Features

### 1. Experiment Modes

#### Binary Classification (`--mode binary`)
- Tests forward vs not-forward classification
- Uses `forward_vs_rest_binary.npy` data file
- 2 classes

#### Multiclass Classification (`--mode multiclass`)
- Tests 4-direction classification (forward, left, right, backward)
- Uses `directions_multiclass.npy` data file
- 4 classes

#### Both Modes (`--mode both`)
- Runs experiments sequentially for both binary and multiclass
- Results saved in separate directories
- Allows comparison across classification tasks

### 2. Split Ratio Testing

The system automatically tests two data split configurations:

- **70/15/15**: 70% training, 15% validation, 15% test
- **80/10/10**: 80% training, 10% validation, 10% test

**Why test split ratios?**
- Different splits can affect model performance
- More training data (80%) may improve generalization
- More validation data (15%) provides better hyperparameter tuning
- Helps identify optimal data distribution

**Results include:**
- Comparison charts showing performance by split ratio
- Best configuration per split ratio
- Statistics aggregated by split ratio

### 3. Hyperparameter Tuning

Enable with `--hyperparameter-tuning` flag.

**What it does:**
- Uses GridSearchCV with 3-fold cross-validation
- Tests multiple hyperparameter combinations per model
- Finds optimal parameters automatically

**Hyperparameter Grids:**

**LogisticRegression:**
- `C`: [0.1, 1.0, 10.0]
- `solver`: ['lbfgs', 'liblinear']
- `penalty`: ['l2']

**DecisionTree:**
- `max_depth`: [10, 20, 30, None]
- `min_samples_split`: [2, 5, 10]
- `min_samples_leaf`: [1, 2, 4]

**SVM:**
- `C`: [0.1, 1.0, 10.0]
- `kernel`: ['rbf', 'linear', 'poly']
- `gamma`: ['scale', 'auto', 0.001, 0.01]

**RandomForest:**
- `n_estimators`: [50, 100, 200]
- `max_depth`: [10, 20, 30, None]
- `min_samples_split`: [2, 5, 10]
- `min_samples_leaf`: [1, 2, 4]

**Note:** Hyperparameter tuning significantly increases experiment time (2-4 hours vs 1-2 hours).

### 4. Quick Mode

Enable with `--quick` flag.

**What it tests:**
- Reduced set of preprocessing configurations (5 instead of 100+)
- All 4 models
- Both split ratios
- **40 total experiments** (vs 800+ in full mode)

**Use cases:**
- Quick validation of setup
- Initial exploration
- Testing new preprocessing techniques
- Development and debugging

### 5. Model Saving

**Automatic Model Persistence:**
- All trained models are automatically saved to `models/` folder
- Each model includes complete preprocessing pipeline + trained model
- Saved as `.pkl` files using `joblib`

**Filename Format:**
```
{ModelName}_{PreprocessingConfig}_{SplitRatio}_{Timestamp}.pkl
```

**Example:**
```
RandomForest_StandardScaler_PCA_70_15_15_20251120_143022.pkl
```

**Model Structure:**
Each saved model is a sklearn Pipeline with two steps:
1. **"preprocessor"**: Complete preprocessing pipeline
2. **"model"**: Trained model

**Usage:**
```python
import joblib

# Load model
model = joblib.load('models/RandomForest_StandardScaler_PCA_70_15_15_20251120_143022.pkl')

# Predict (preprocessing included)
predictions = model.predict(X_new_data)
probabilities = model.predict_proba(X_new_data)
```

**Benefits:**
- No need to retrain models
- Reproducible results
- Easy model comparison
- Production-ready models

### 6. Results Output

**Location:**
- Results saved to `results/experiments_{mode}_{timestamp}/`
- Models saved to `models/` (project root)

**Files Generated:**

1. **`all_experiments_*.csv`**
   - Complete results table
   - Columns: preprocessing, model, split_ratio, accuracy, f1_score, roc_auc, model_path, etc.
   - Can be opened in Excel/LibreOffice

2. **`best_configurations_*.txt`**
   - Text report of best configurations
   - Overall best, best by metric, best per model, best per split ratio

3. **`summary_statistics_*.txt`**
   - Statistical analysis
   - Mean, std, min, max for all metrics
   - Breakdown by model, preprocessing type, split ratio

4. **`heatmaps_*.png`**
   - 4 heatmaps showing preprocessing × model performance
   - Metrics: Accuracy, F1-Score, ROC-AUC, Training Time
   - Averaged across split ratios

5. **`split_ratio_comparison_*.png`**
   - Visual comparison of 70/15/15 vs 80/10/10
   - 4 charts: Accuracy, F1-Score, ROC-AUC, Training Time

6. **`top_configs_*.png`**
   - Bar chart of top 15 configurations
   - Includes split ratio information
   - Color-coded by model type

7. **`all_experiments_*.json`**
   - Raw JSON data
   - Includes all metrics, parameters, model paths
   - For programmatic analysis

## Command Line Options

```bash
poetry run python modulus/run_preprocessing_experiments.py [OPTIONS]

Options:
  --mode {binary,multiclass,both}
                        Classification mode (default: multiclass)
  --quick               Run quick mode (fewer experiments, faster)
  --hyperparameter-tuning
                        Enable hyperparameter tuning with GridSearchCV
  --output OUTPUT       Output directory (default: results/experiments/)
  --data DATA           Path to prepared data directory (default: data/prepared/)
```

## Pygame UI Integration

Experiments can also be run through the interactive Pygame interface:

1. Launch: `poetry run python -m trainer.main`
2. Press `[M]` to enter ModulusScene
3. Configure:
   - `[UP]/[DOWN]` - Select mode (Binary/Multiclass/Both)
   - `[Q]` - Toggle Quick Mode
   - `[H]` - Toggle Hyperparameter Tuning
4. Press `[ENTER]` to run
5. View progress and results in real-time

## Example Workflows

### Quick Exploration
```bash
# Quick test to validate setup
poetry run python modulus/run_preprocessing_experiments.py --mode binary --quick
```

### Full Analysis
```bash
# Complete analysis with hyperparameter tuning
poetry run python modulus/run_preprocessing_experiments.py \
  --mode multiclass \
  --hyperparameter-tuning \
  --output results/full_analysis/
```

### Compare Both Modes
```bash
# Test both binary and multiclass
poetry run python modulus/run_preprocessing_experiments.py --mode both
```

### Use Saved Models
```python
import joblib
import pandas as pd

# Load best model from results CSV
results = pd.read_csv('results/experiments_multiclass_*/all_experiments_*.csv')
best = results.loc[results['accuracy'].idxmax()]
model_path = best['model_path']

# Load and use
model = joblib.load(model_path)
predictions = model.predict(X_new)
```

## Performance Considerations

### Experiment Counts

| Mode | Preprocessing Configs | Models | Split Ratios | Total Experiments |
|------|----------------------|--------|--------------|-------------------|
| Quick | 5 | 4 | 2 | 40 |
| Full | 100+ | 4 | 2 | 800+ |
| Full + Tuning | 100+ | 4 | 2 | 800+ (with CV) |

### Estimated Times

| Mode | Time Estimate |
|------|---------------|
| Quick | 5-10 minutes |
| Full | 1-2 hours |
| Full + Tuning | 2-4 hours |

Times depend on:
- Dataset size
- CPU cores (uses `n_jobs=-1` for parallelization)
- Preprocessing complexity
- Model complexity

## Best Practices

1. **Start with Quick Mode**: Validate setup before running full experiments
2. **Use Hyperparameter Tuning**: For final model selection, enable tuning
3. **Check Split Ratio Comparison**: Determine optimal data split
4. **Save Models**: All models are automatically saved - use them!
5. **Review Visualizations**: Heatmaps and charts reveal patterns
6. **Compare Modes**: Run both binary and multiclass to understand differences

## Troubleshooting

### Issue: Out of Memory
**Solution**: Use `--quick` mode or reduce preprocessing configurations

### Issue: Experiments Taking Too Long
**Solution**: 
- Use `--quick` for faster results
- Disable `--hyperparameter-tuning` if not needed
- Reduce number of preprocessing configs in code

### Issue: Models Not Saving
**Solution**: Check that `models/` directory exists and is writable

### Issue: Split Ratio Results Identical
**Solution**: This is normal if dataset is small or well-balanced. Check dataset size.

## Related Documentation

- `docs/modulus/status/EXPERIMENTS_COMPLETE.md` - Overview and quick start
- `docs/modulus/QUICKSTART.md` - General quick start guide
- `modulus/run_preprocessing_experiments.py` - Implementation code

