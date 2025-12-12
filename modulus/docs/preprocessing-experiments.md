# Comprehensive Preprocessing Experiments

This guide explains how to systematically test all combinations of preprocessing techniques and models to find the optimal configuration for your data.

## Quick Summary

**Tool**: `run_preprocessing_experiments.py`

**Purpose**: Automatically tests all combinations of:
- Preprocessing techniques (none, scaling, PCA, feature extraction, EEG filters, etc.)
- Models (Logistic Regression, Decision Tree, SVM, Random Forest)
- Data split ratios (70/15/15 and 80/10/10)

**Output**: Detailed comparison with visualizations, best model selection, and test set evaluation.

## New Optimized Workflow ⭐

The latest version uses an **optimized two-phase approach**:

### Phase 1: Baseline Validation
- Tests ALL configurations with default parameters
- Uses **cached transforms** (preprocessing fitted once per split)
- Fast parallel execution
- Selects **top K configurations** by F1-score

### Phase 2: Hyperparameter Tuning (Optional)
- Only tunes the **top K** promising configurations
- GridSearchCV with configurable CV folds
- 80%+ time savings vs tuning everything

## Quick Start

### Run Quick Test (72 experiments, ~5-10 minutes)

```bash
poetry run python run_preprocessing_experiments.py --quick
```

Tests 9 key preprocessing configurations × 4 models × 2 split ratios = 72 experiments

### Run Full Comprehensive Test (~800+ experiments, 30-60 minutes)

```bash
poetry run python run_preprocessing_experiments.py
```

Tests 100+ preprocessing configurations × 4 models × 2 split ratios = 800+ experiments

### Run with Optimized Tuning

```bash
# Two-phase: baseline → tune top 15
poetry run python run_preprocessing_experiments.py --hyperparameter-tuning --top-k 15
```

### Run with Parallel CPUs

```bash
# Use 8 workers (experiments in parallel)
poetry run python run_preprocessing_experiments.py --n-jobs 8
```

## What Gets Tested

### Quick Mode (--quick flag)

**Standard preprocessing:**
1. **None** - No preprocessing baseline
2. **StandardScaler** - Just normalization
3. **StandardScaler+PCA100** - Normalization + dimensionality reduction
4. **FeatureExtraction+Scaler** - Extract mean, std, energy
5. **AllFeatures+Scaler+PCA50** - Extract all statistical features + PCA

**EEG-specific preprocessing (NEW):**
6. **NotchFilter50Hz+Scaler** - Remove power line noise
7. **BandPass0.5-40Hz+Scaler** - Filter EEG frequency band
8. **FullEEG+Features** - Complete EEG pipeline (notch + bandpass + smoothing + features)
9. **FullEEG+Artifacts+Features** - Full pipeline with artifact rejection

### Full Mode (default)

Tests combinations of:

#### 1. Scaling Options
- None
- StandardScaler
- RobustScaler

#### 2. Dimensionality Reduction
- None
- PCA with 50 components
- PCA with 100 components
- PCA with 200 components

#### 3. Feature Extraction
- Mean + Std
- Mean + Std + Energy
- Mean + Std + Energy + Range
- All features (mean, std, energy, range, min, max)

#### 4. Time-Series Preprocessing
- Downsampling (2x, 4x)
- Moving average (window 3, 5)

#### 5. Combinations
- Feature extraction + scaling + PCA
- Downsampling + scaling + PCA
- Moving average + scaling + PCA

**Total**: 100+ unique preprocessing pipelines

## Performance Optimizations

### Caching System

The system uses intelligent caching to avoid redundant computation:

1. **Split Caching**: Data splits computed once per ratio, reused across all experiments
2. **Transform Caching**: Preprocessing pipelines cached per (split, preprocessing) pair
3. **Float32 Conversion**: Data converted to float32 for faster math

### Parallel Execution

- Uses `spawn` multiprocessing context (avoids fork deadlocks)
- Configurable worker count (`--n-jobs N`)
- Thread caps for BLAS/OpenMP to prevent oversubscription
- Progress bar with tqdm for visibility

### Selective Tuning

- Only top K configurations proceed to expensive tuning phase
- Default: top 15 by F1-score (with Recall > 0 filter)
- 80%+ time savings compared to tuning everything

## Command Options

```bash
poetry run python run_preprocessing_experiments.py [OPTIONS]

Options:
  --mode {binary,multiclass,both}
                        Classification mode (default: multiclass)
  --quick               Run quick mode (9 configs, 72 experiments)
  --hyperparameter-tuning
                        Enable two-phase tuning (tune top K only)
  --top-k N             Number of top configs to tune (default: 15)
  --cv-folds N          CV folds for GridSearchCV (default: 5)
  --n-jobs N            Number of parallel workers (default: all CPUs)
  --output OUTPUT       Output directory
  --data DATA           Path to prepared data directory
```

## Generated Reports

After running experiments, you'll get:

### 1. All Experiments CSV
**File**: `results/experiments_*/all_experiments_TIMESTAMP.csv`

Complete table with all results including model paths.

### 2. Best Configurations Report
**File**: `results/experiments_*/best_configurations_TIMESTAMP.txt`

Uses **F1-score ranking with Recall > 0 filter** to find meaningful configurations.

### 3. Test Set Evaluation ⭐ NEW
**File**: `results/experiments_*/test_set_evaluation_TIMESTAMP.txt`

Final evaluation on held-out test set:
- Validation vs test comparison
- Generalization gap analysis

### 4. Best Model ⭐ NEW
**File**: `results/experiments_*/best_model.pkl`

Ready-to-use sklearn Pipeline with preprocessing + model.

### 5. Visualizations
- `heatmaps_*.png` - Preprocessing × Model performance
- `split_ratio_comparison_*.png` - 70/15/15 vs 80/10/10
- `top_configs_*.png` - Bar chart of top configurations

## Model Selection Criteria

The system uses intelligent selection:

1. **Filter**: Models with Recall > 0 (excludes trivial classifiers)
2. **Rank**: By F1-score (descending)
3. **Tiebreaker**: ROC-AUC score

This ensures selected models have meaningful predictive capability.

## Example Workflows

### Quick Exploration
```bash
poetry run python run_preprocessing_experiments.py --mode binary --quick
```

### Full Analysis with Tuning
```bash
poetry run python run_preprocessing_experiments.py \
  --mode multiclass \
  --hyperparameter-tuning \
  --top-k 15 \
  --cv-folds 5
```

### Compare Both Modes
```bash
poetry run python run_preprocessing_experiments.py --mode both
```

### Use Best Model
```python
import joblib

# Load best model (includes preprocessing)
model = joblib.load('results/experiments_multiclass_*/best_model.pkl')

# Predict on new data
predictions = model.predict(X_new)
probabilities = model.predict_proba(X_new)
```

## Using the Pygame GUI

1. Launch: `poetry run python main.py`
2. Press `[M]` for ML Pipeline
3. Configure:
   - `[UP/DOWN]` - Select mode
   - `[Q]` - Quick mode
   - `[H]` - Hyperparameter tuning
   - `[T/Y]` - Adjust top-K
   - `[F/G]` - Adjust CV folds
   - `[+/-]` - CPU count
4. Press `[ENTER]` to run
5. Watch progress bar and phase indicator

## Estimated Times

| Mode | Baseline | + Tuning (top 15) | Total |
|------|----------|-------------------|-------|
| Quick | 5-10 min | +10-20 min | 15-30 min |
| Full | 30-60 min | +30-60 min | 1-2 hours |

## Troubleshooting

### Out of memory
```bash
poetry run python run_preprocessing_experiments.py --quick --n-jobs 4
```

### Taking too long
- Use `--quick` flag
- Reduce `--top-k` for tuning
- Reduce `--cv-folds`

### All models have zero recall
- Check data quality and class balance
- Verify data preparation step

## Summary

**Key Features:**
1. ✅ Two-phase optimized workflow
2. ✅ Transform caching for speed
3. ✅ Intelligent model selection (F1 + Recall filter)
4. ✅ Test set evaluation for true performance
5. ✅ Best model saved ready for inference
6. ✅ EEG-specific preprocessing options

**Files Generated:**
- `all_experiments_*.csv` - Complete results
- `best_configurations_*.txt` - Top configs
- `test_set_evaluation_*.txt` - Test performance
- `best_model.pkl` - Ready-to-use model
- `heatmaps_*.png` - Visual comparison

---

**Ready to find your best preprocessing?**

```bash
# Quick start
poetry run python run_preprocessing_experiments.py --quick

# Full with tuning
poetry run python run_preprocessing_experiments.py --hyperparameter-tuning
```
