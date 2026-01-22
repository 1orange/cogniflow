# Preprocessing Experiment Features

This document describes all features available in the comprehensive preprocessing experiment system.

## Overview

The preprocessing experiment system (`modulus/run_preprocessing_experiments.py`) automatically tests all combinations of preprocessing techniques, models, and data split ratios to find optimal configurations.

**Key improvements in the latest version:**
- **Optimized Two-Phase Workflow**: Baseline validation → Selective hyperparameter tuning
- **Transform Caching**: Preprocessing pipelines are cached to avoid redundant computation
- **Top-K Selection**: Only the best configurations proceed to tuning phase
- **Parallel Execution**: Full multiprocessing support with spawn context

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

### 2. Optimized Two-Phase Workflow

When hyperparameter tuning is enabled, the system uses an optimized two-phase approach:

#### Phase 1: Baseline Validation
- Runs ALL preprocessing + model combinations with default parameters
- Uses precomputed data splits (cached for efficiency)
- Caches transformed data per (split, preprocessing) pair
- Evaluates on validation set
- Selects **top K configurations** by F1-score (with Recall > 0 filter)

#### Phase 2: Hyperparameter Tuning
- Only tunes the **top K configurations** from Phase 1
- Uses GridSearchCV with configurable CV folds
- Finds optimal hyperparameters for promising configurations
- Saves tuned models with improved performance

**Benefits:**
- Avoids expensive tuning on poor configurations
- 80%+ reduction in tuning time compared to tuning everything
- Better resource allocation to promising candidates

### 3. Split Ratio Testing

The system automatically tests two data split configurations:

- **70/15/15**: 70% training, 15% validation, 15% test
- **80/10/10**: 80% training, 10% validation, 10% test

**Splits are precomputed once** and reused across all experiments for consistency and speed.

**Results include:**
- Comparison charts showing performance by split ratio
- Best configuration per split ratio
- Statistics aggregated by split ratio

### 4. Top-K Selection

Control how many configurations proceed to hyperparameter tuning:

- **CLI**: `--top-k N` (default: 15)
- **GUI**: Use `[T]/[Y]` keys to adjust (5-30 range)

**Selection criteria:**
1. Filter models with Recall > 0 (excludes trivial majority-class predictors)
2. Rank by F1-score (descending)
3. Use ROC-AUC as tiebreaker

### 5. Hyperparameter Tuning

Enable with `--hyperparameter-tuning` flag.

**What it does:**
- Uses GridSearchCV with configurable cross-validation
- Tests multiple hyperparameter combinations per model
- Finds optimal parameters automatically
- **Only tunes top K configurations** (optimized workflow)

**CV Folds:**
- **CLI**: `--cv-folds N` (default: 5, range: 3-10)
- **GUI**: Use `[F]/[G]` keys to adjust

**Hyperparameter Grids:**

**LogisticRegression:**
- `C`: [0.1, 1.0, 10.0]
- `solver`: ['lbfgs', 'liblinear']

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

### 6. Quick Mode

Enable with `--quick` flag.

**What it tests:**
- Reduced set of preprocessing configurations (9 instead of 100+)
- Includes EEG-specific preprocessing (notch filter, bandpass, artifact rejection)
- All 4 models
- Both split ratios
- **72 total experiments** (vs 800+ in full mode)

**Use cases:**
- Quick validation of setup
- Initial exploration
- Testing new preprocessing techniques
- Development and debugging

### 7. Parallel Execution

**CLI:** `--n-jobs N` runs experiments in parallel using multiprocessing.
- Default: Use all available CPUs
- Set to `1` to disable parallelization

**GUI:** Use `[+]/[-]` to adjust CPU count before running.

**Implementation details:**
- Uses `spawn` multiprocessing context (avoids fork-related deadlocks)
- GridSearchCV inside each worker uses `n_jobs=1` to avoid nested parallelism
- Progress bar with tqdm for visibility
- Timeout support for stuck experiments (5 min baseline, 10 min tuning)

### 8. Performance Optimizations

**No reduction in test coverage:**

1. **Precomputed splits**: Each split ratio computed once and reused
2. **Transform caching**: Preprocessing pipelines cached per (split, preprocessing) pair
3. **Float32 data**: Datasets converted to float32 for faster math
4. **Thread caps**: Environment defaults set (`OMP_NUM_THREADS=1`, etc.) to prevent oversubscription
5. **Selective tuning**: Only top K configurations proceed to expensive tuning phase

### 9. Model Selection Criteria

The system uses intelligent model selection:

1. **Filter**: Models with Recall > 0 (excludes trivial classifiers)
2. **Rank**: By F1-score (descending)
3. **Tiebreaker**: ROC-AUC score

This ensures selected models have meaningful predictive capability, not just high accuracy from majority-class prediction.

### 10. Test Set Evaluation

After experiments complete:
- Best model automatically evaluated on held-out test set
- Provides unbiased performance estimate
- Compares validation vs test metrics (generalization gap)
- Results saved to `test_set_evaluation_*.txt`

### 11. Model Saving

**Automatic Model Persistence:**
- All trained models saved to `models/` folder
- Each model includes complete preprocessing pipeline + trained model
- Saved as `.pkl` files using `joblib`

**Best Model:**
- After analysis, best model is copied to `results/experiments_*/best_model.pkl`
- Other model files are cleaned up to save space

**Filename Format:**
```
{ModelName}_{PreprocessingConfig}_{SplitRatio}_{Timestamp}.pkl
```

**Model Structure:**
Each saved model is a sklearn Pipeline with two steps:
1. **"preprocessor"**: Complete preprocessing pipeline
2. **"model"**: Trained model

**Usage:**
```python
import joblib

# Load model
model = joblib.load('results/experiments_multiclass_*/best_model.pkl')

# Predict (preprocessing included)
predictions = model.predict(X_new_data)
probabilities = model.predict_proba(X_new_data)
```

### 12. Results Output

**Location:**
- Results saved to `results/experiments_{mode}_{timestamp}/`
- Best model saved to `results/experiments_*/best_model.pkl`

**Files Generated:**

1. **`all_experiments_*.csv`**
   - Complete results table
   - Columns: preprocessing, model, split_ratio, accuracy, f1_score, roc_auc, model_path, etc.

2. **`best_configurations_*.txt`**
   - Text report of best configurations
   - Uses F1-score ranking with Recall > 0 filter
   - Overall best, best by metric, best per model, best per split ratio

3. **`test_set_evaluation_*.txt`** ⭐ NEW
   - Final evaluation on held-out test set
   - Validation vs test comparison
   - Generalization gap analysis

4. **`summary_statistics_*.txt`**
   - Statistical analysis
   - Mean, std, min, max for all metrics
   - Breakdown by model, preprocessing type, split ratio

5. **`heatmaps_*.png`**
   - 4 heatmaps showing preprocessing × model performance
   - Metrics: Accuracy, F1-Score, ROC-AUC, Training Time

6. **`split_ratio_comparison_*.png`**
   - Visual comparison of 70/15/15 vs 80/10/10

7. **`top_configs_*.png`**
   - Bar chart of top 15 configurations

8. **`all_experiments_*.json`**
   - Raw JSON data for programmatic analysis

9. **`best_model.pkl`** ⭐ NEW
   - Best trained model (complete pipeline)
   - Ready for inference

## Command Line Options

```bash
poetry run python modulus/run_preprocessing_experiments.py [OPTIONS]

Options:
  --mode {binary,multiclass,both}
                        Classification mode (default: multiclass)
  --quick               Run quick mode (fewer experiments, faster)
  --hyperparameter-tuning
                        Enable hyperparameter tuning (two-phase workflow)
  --top-k N             Top K configs to tune (default: 15)
  --cv-folds N          CV folds for GridSearchCV (default: 5)
  --n-jobs N            Number of parallel workers (default: all CPUs)
  --output OUTPUT       Output directory (default: results/experiments_{mode}/)
  --data DATA           Path to prepared data directory (default: data/prepared/)
```

## Pygame UI Integration

Experiments can also be run through the interactive Pygame interface:

1. Launch: `poetry run python main.py`
2. Press `[M]` to enter ModulusScene
3. Configure:
   - `[UP]/[DOWN]` — Select mode (Binary/Multiclass/Both)
   - `[Q]` — Toggle Quick Mode
   - `[H]` — Toggle Hyperparameter Tuning
   - `[T]/[Y]` — Adjust Top-K (when tuning enabled)
   - `[F]/[G]` — Adjust CV Folds (when tuning enabled)
   - `[+]/[-]` — Adjust CPU count
4. Press `[ENTER]` to run
5. View progress bar and phase indicator
6. Results saved to `results/` folder

**UI Features:**
- Progress bar with percentage
- Phase indicator (Baseline → Tuning)
- Workflow description based on settings
- Real-time status updates

## Model Browser ⭐ NEW

The GUI includes a built-in model browser to view and load trained models:

### Accessing the Browser
- Press `[B]` from any screen to toggle between **Experiments Mode** and **Browse Mode**

### Browse Mode Features
- Lists all models from:
  - `results/*/best_model.pkl` — Best models from each experiment run
  - `models/*.pkl` — Individual model files
- Shows model metadata:
  - Model type (RandomForest, SVM, etc.)
  - Preprocessing configuration
  - Accuracy and F1-score (when available)
  - Data split ratio

### Browse Mode Controls

| Key | Action |
|-----|--------|
| `[UP/DOWN]` | Navigate model list |
| `[PAGE UP/DOWN]` | Navigate by page |
| `[HOME/END]` | Jump to first/last model |
| `[ENTER]` | Load selected model |
| `[C]` | Copy model to `models/model.pkl` |
| `[R]` | Refresh model list |
| `[B]` | Back to experiments mode |
| `[ESC]` | Exit ModulusScene |

### Using Loaded Models

**Copy to model.pkl for Driving:**
1. Select a model in browse mode
2. Press `[C]` to copy to `models/model.pkl`
3. Return to menu and use **Drive (BCI)** mode

**Load for Inspection:**
1. Select a model
2. Press `[ENTER]` to load
3. Model details shown in the UI

## Example Workflows

### Quick Exploration
```bash
# Quick test to validate setup
poetry run python modulus/run_preprocessing_experiments.py --mode binary --quick
```

### Full Analysis with Optimized Tuning
```bash
# Complete analysis with selective hyperparameter tuning
poetry run python modulus/run_preprocessing_experiments.py \
  --mode multiclass \
  --hyperparameter-tuning \
  --top-k 15 \
  --cv-folds 5 \
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

# Load best model from results
model = joblib.load('results/experiments_multiclass_*/best_model.pkl')

# Or load specific model
model = joblib.load('models/RandomForest_FullEEG_70_15_15_20251212.pkl')

# Predict on new data
predictions = model.predict(X_new)
probabilities = model.predict_proba(X_new)
```

## Performance Considerations

### Experiment Counts

| Mode | Preprocessing | Models | Splits | Baseline | Tuning (top 15) |
|------|---------------|--------|--------|----------|-----------------|
| Quick | 9 | 4 | 2 | 72 | 30 |
| Full | 100+ | 4 | 2 | 800+ | 30 |

### Estimated Times

| Mode | Baseline | + Tuning | Total |
|------|----------|----------|-------|
| Quick | 5-10 min | +10-20 min | 15-30 min |
| Full | 30-60 min | +30-60 min | 1-2 hours |

Times depend on:
- Dataset size
- CPU cores (parallelization)
- Preprocessing complexity
- Top-K setting for tuning

## Best Practices

1. **Start with Quick Mode**: Validate setup before running full experiments
2. **Use Two-Phase Tuning**: Enable `--hyperparameter-tuning` for optimal results
3. **Adjust Top-K**: Increase for more thorough tuning, decrease for speed
4. **Check Test Evaluation**: Review `test_set_evaluation_*.txt` for true performance
5. **Review Visualizations**: Heatmaps and charts reveal patterns
6. **Compare Modes**: Run both binary and multiclass to understand differences

## Troubleshooting

### Issue: Out of Memory
**Solution**: Use `--quick` mode or reduce `--n-jobs`

### Issue: Experiments Taking Too Long
**Solution**: 
- Use `--quick` for faster results
- Reduce `--top-k` to tune fewer configurations
- Reduce `--cv-folds` for faster cross-validation

### Issue: Models Not Saving
**Solution**: Check that `models/` and `results/` directories exist and are writable

### Issue: All Models Have Zero Recall
**Solution**: This indicates class imbalance issues. Check your data preparation.

### Issue: Timeout Errors
**Solution**: Some configurations may be too slow. The system automatically handles timeouts (5 min baseline, 10 min tuning) and continues with remaining experiments.

## Related Documentation

- [Modulus Quick Start](../../modulus/docs/quick-start.md)
- [Preprocessing Modes](../../modulus/docs/preprocessing-modes.md)
- [Custom Preprocessing](../../modulus/docs/custom-preprocessing.md)
- [Main README](../../README.md)
