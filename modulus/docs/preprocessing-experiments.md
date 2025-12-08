# Comprehensive Preprocessing Experiments

This guide explains how to systematically test all combinations of preprocessing techniques and models to find the optimal configuration for your data.

## Quick Summary

**Tool**: `run_preprocessing_experiments.py`

**Purpose**: Automatically tests all combinations of:
- Preprocessing techniques (none, scaling, PCA, feature extraction, downsampling, etc.)
- Models (Logistic Regression, Decision Tree, SVM, Random Forest)

**Output**: Detailed comparison with visualizations showing which combination works best.

## Quick Start

### Run Quick Test (20 experiments, ~3 minutes)

```bash
poetry run python run_preprocessing_experiments.py --quick
```

Tests 5 key preprocessing configurations × 4 models = 20 experiments

### Run Full Comprehensive Test (~100+ experiments, 30-60 minutes)

```bash
poetry run python run_preprocessing_experiments.py
```

Tests 100+ preprocessing configurations × 4 models = 400+ experiments

## What Gets Tested

### Quick Mode (--quick flag)

1. **None** - No preprocessing baseline
2. **StandardScaler** - Just normalization
3. **StandardScaler+PCA100** - Normalization + dimensionality reduction
4. **FeatureExtraction+Scaler** - Extract mean, std, energy
5. **AllFeatures+Scaler+PCA50** - Extract all statistical features + PCA

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

## Results from Quick Test

### Best Configuration Found

```
🏆 WINNER: Feature Extraction + SVM
   - Accuracy: 56.65%
   - F1-Score: 51.82%
   - ROC-AUC: 82.09%
   - Features: 42 (reduced from 2688!)
   - Training time: 2.5 seconds
   
Configuration:
   - Extract: mean, std, energy per channel
   - Scale: StandardScaler
   - Model: SVM with RBF kernel
```

### Top 5 Configurations

| Rank | Preprocessing | Model | Accuracy | Features |
|------|---------------|-------|----------|----------|
| 1 | FeatureExtraction+Scaler | SVM | 56.65% | 42 |
| 2 | AllFeatures+Scaler+PCA50 | SVM | 54.37% | 50 |
| 3 | FeatureExtraction+Scaler | RandomForest | 51.52% | 42 |
| 4 | AllFeatures+Scaler+PCA50 | DecisionTree | 49.81% | 50 |
| 5 | StandardScaler+PCA100 | RandomForest | 49.62% | 100 |

### Key Insights

1. **Feature extraction is crucial**
   - Extracting statistical features (mean, std, energy) improves accuracy by 10+ percentage points
   - Reduces features from 2688 → 42 (98% reduction!)
   - Faster training and better generalization

2. **SVM works best**
   - SVM achieves highest accuracy with feature extraction
   - ROC-AUC of 82% shows good class separability

3. **Dimensionality reduction helps**
   - Raw 2688 features → only 46% accuracy
   - Reduced features (42-100) → 50-57% accuracy
   - Less is more!

4. **No preprocessing is worst**
   - Baseline (no preprocessing) gives only 46.58% accuracy
   - Any preprocessing helps

## Generated Reports

After running experiments, you'll get:

### 1. All Experiments CSV
**File**: `results/experiments/all_experiments_TIMESTAMP.csv`

Complete table with all results:
```csv
preprocessing,model,accuracy,precision,recall,f1_score,roc_auc,n_features_out,time_seconds,status
FeatureExtraction+Scaler,SVM,0.5665,0.5814,0.5665,0.5182,0.8209,42,2.50,success
...
```

### 2. Best Configurations Report
**File**: `results/experiments/best_configurations_TIMESTAMP.txt`

Text report showing:
- Overall best configuration
- Best by F1-score
- Best by ROC-AUC
- Top 10 configurations
- Best preprocessing per model
- Best model per preprocessing

### 3. Summary Statistics
**File**: `results/experiments/summary_statistics_TIMESTAMP.txt`

Statistical analysis:
- Mean, std, min, max for all metrics
- Statistics by model
- Statistics by preprocessing type

### 4. Heatmaps
**File**: `results/experiments/heatmaps_TIMESTAMP.png`

4 heatmaps showing:
- Accuracy: Preprocessing × Model
- F1-Score: Preprocessing × Model
- ROC-AUC: Preprocessing × Model
- Training time: Preprocessing × Model

### 5. Top Configurations Chart
**File**: `results/experiments/top_configs_TIMESTAMP.png`

Bar chart of top 15 configurations, color-coded by model.

### 6. JSON Data
**File**: `results/experiments/all_experiments_TIMESTAMP.json`

Machine-readable format for further analysis.

## Command Options

```bash
# Quick test (5 configs, 20 experiments)
poetry run python run_preprocessing_experiments.py --quick

# Full test (100+ configs, 400+ experiments)
poetry run python run_preprocessing_experiments.py

# Custom output directory
poetry run python run_preprocessing_experiments.py --output my_results/

# Custom data location
poetry run python run_preprocessing_experiments.py --data data/prepared/

# Combined
poetry run python run_preprocessing_experiments.py --quick --output results/quick_test/
```

## Interpreting Results

### Accuracy

- **Baseline (25%)**: Random guessing for 4 classes
- **Good (50-60%)**: Significant improvement
- **Excellent (>70%)**: Very good performance

**Current best**: 56.65% (2.26x better than random)

### ROC-AUC

- **0.5**: Random classifier
- **0.7-0.8**: Good
- **0.8-0.9**: Very good
- **>0.9**: Excellent

**Current best**: 82.09% (very good!)

### Feature Count

- **Original**: 2688 features (192 timesteps × 14 channels)
- **Best**: 42 features (3 statistics × 14 channels)
- **Reduction**: 98.4% fewer features, better accuracy!

### Training Time

- **< 5 seconds**: Fast
- **5-30 seconds**: Moderate
- **30-120 seconds**: Slow (SVM with many features)

**Best model**: 2.5 seconds (fast!)

## How It Works

### Process Flow

```
1. Load data once
   └─ Split into train/val/test

2. For each preprocessing config:
   └─ For each model:
      ├─ Build preprocessing pipeline
      ├─ Transform training data
      ├─ Train model
      ├─ Evaluate on validation set
      └─ Record metrics

3. Analyze results
   ├─ Find best configurations
   ├─ Generate visualizations
   ├─ Compute statistics
   └─ Create reports
```

### Preprocessing Pipeline Example

```python
# Example: Feature Extraction + Scaler
Pipeline([
    ('feature_extraction', TimeSeriesFeatureExtractor(
        n_timesteps=192,
        n_channels=14,
        features=['mean', 'std', 'energy']
    )),
    ('scaler', StandardScaler()),
])
```

Transforms:
- Input: (n_samples, 2688) - raw flattened data
- After extraction: (n_samples, 42) - 3 features × 14 channels
- After scaling: (n_samples, 42) - normalized

## Recommendations Based on Results

### For Your Forward Direction Data

1. **Use Feature Extraction**
   ```yaml
   Preprocessing:
     extract_features: true
     feature_list:
       - mean
       - std
       - energy
     standard_scaler: true
   ```

2. **Use SVM Model**
   ```yaml
   Models:
     - name: SVM
       params:
         kernel: rbf
         C: 1.0
         probability: true
   ```

3. **Expected Performance**
   - Accuracy: ~57%
   - ROC-AUC: ~82%
   - Training time: < 3 seconds

### Why Feature Extraction Works

#### Raw Data Issues
- 2688 features = high dimensionality
- Many features are correlated
- Noise in individual timepoints
- Curse of dimensionality

#### Feature Extraction Benefits
- Summarizes temporal patterns
- Reduces noise through aggregation
- Captures essential characteristics
- Much faster to train
- Better generalization

## Advanced Usage

### Add Your Own Preprocessing

Edit `run_preprocessing_experiments.py`:

```python
def define_preprocessing_configs(self, quick=False):
    configs = [
        # ... existing configs ...
        
        # Add your custom config
        {
            'name': 'MyCustomPreprocessing',
            'use_my_custom': True,
            'my_custom_param': 15,
            'standard_scaler': True,
        },
    ]
    return configs
```

### Filter Experiments

Modify the code to test specific combinations:

```python
# Test only SVM and RandomForest
def define_models(self):
    return [
        ModelSpec(name="SVM", params={...}),
        ModelSpec(name="RandomForest", params={...}),
    ]
```

### Custom Metrics

Add your own evaluation metrics in `run_single_experiment()`:

```python
result = {
    # ... existing metrics ...
    'my_custom_metric': compute_my_metric(y_true, y_pred),
}
```

## Comparison with Original Results

### Before Experiments (Single Config)

```
Random Forest + StandardScaler + PCA100
- Accuracy: 50.00%
- ROC-AUC: 75.43%
- Features: 100
```

### After Experiments (Best Found)

```
SVM + Feature Extraction + StandardScaler
- Accuracy: 56.65% (+6.65%)
- ROC-AUC: 82.09% (+6.66%)
- Features: 42 (58% fewer features!)
```

**Improvement**: 13% better accuracy, 9% better ROC-AUC, faster training!

## Next Steps

1. **Run full experiments**:
   ```bash
   poetry run python run_preprocessing_experiments.py
   ```

2. **Review heatmaps**:
   ```bash
   xdg-open results/experiments/heatmaps_*.png
   ```

3. **Implement best config**:
   - Update `config/forward_direction_config.yaml`
   - Set feature extraction + SVM
   - Run final pipeline

4. **Test on test set**:
   - Use best config from experiments
   - Evaluate on held-out test data
   - Report final performance

## Troubleshooting

### Out of memory

Reduce configurations:
```bash
poetry run python run_preprocessing_experiments.py --quick
```

### Taking too long

- Use `--quick` flag
- Reduce number of models
- Skip slow configurations (high-dim SVM)

### Low accuracy everywhere

- Check data quality
- Verify labels are correct
- Try different preprocessing
- Consider data augmentation

## Summary

**Key Takeaways:**
1. ✅ Feature extraction > Raw data
2. ✅ SVM > Other models (for this data)
3. ✅ Fewer features often better
4. ✅ Always test multiple configurations
5. ✅ 56.65% accuracy achieved (vs 46.58% baseline)

**Files Generated:**
- `all_experiments_*.csv` - Complete results
- `best_configurations_*.txt` - Top configs
- `heatmaps_*.png` - Visual comparison
- `top_configs_*.png` - Bar chart
- `summary_statistics_*.txt` - Stats

**Time Investment:**
- Quick test: 3-5 minutes
- Full test: 30-60 minutes
- Analysis: Automated

**Value:**
- Find optimal configuration
- Understand what works
- Scientific comparison
- Reproducible results

---

**Ready to find your best preprocessing?**

```bash
poetry run python run_preprocessing_experiments.py --quick
```

