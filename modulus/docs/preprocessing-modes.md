# Preprocessing Modes: Forward-Only vs Multiclass

This document explains the two data preparation modes available in the Modulus framework and when to use each one.

## Overview

The `prepare_direction_data.py` script supports two modes for preparing your EEG direction data:

1. **Forward-Only Mode**: Prepares only forward direction data (single-class)
2. **Multiclass Mode**: Prepares all direction data (multi-class classification)

## Forward-Only Mode

### Description

In forward-only mode, the script loads only the forward direction data and labels all samples as class 1 (forward).

### Command

```bash
poetry run python prepare_direction_data.py --mode forward-only
```

### Output

Creates `data/forward_prepared.npy` with:
- **690 samples** (all from forward direction)
- **2688 features** (192 timesteps × 14 channels, flattened)
- **All labels = 1** (indicating "forward")
- **Metadata**: sample_id, direction, window_index, n_timesteps, n_channels

### Data Structure

```python
{
    'features': np.ndarray,  # Shape: (690, 2688)
    'labels': np.ndarray,    # Shape: (690,) - all values are 1
    'metadata': pd.DataFrame # 690 rows with metadata
}
```

### Use Cases

**❌ Not Recommended for Classification**

Forward-only mode creates a dataset where all samples have the same label. This is **not suitable for supervised learning** because:
- Models have nothing to distinguish between
- No meaningful classification can be learned
- Metrics like accuracy are meaningless (always 100% if predicting class 1)

**✓ When to Use**

Forward-only mode is useful for:
1. **Feature extraction experiments**: Testing different preprocessing techniques on forward data
2. **Anomaly detection**: Using forward as "normal" and detecting deviations
3. **Baseline analysis**: Understanding the characteristics of forward-only samples
4. **Data inspection**: Examining forward direction properties in isolation

### Example Configuration

```yaml
Data:
  source: data/
  # Will load forward_prepared.npy
  feature_key: features
  target_key: labels
  
Preprocessing:
  # Since all samples are identical class, focus on feature engineering
  extract_features: true
  feature_list:
    - mean
    - std
    - energy
```

---

## Multiclass Mode (Recommended)

### Description

In multiclass mode, the script loads all four direction datasets (backward, forward, left, right) and assigns unique class labels to each direction.

### Command

```bash
poetry run python prepare_direction_data.py --mode multiclass
```

### Output

Creates `data/directions_multiclass.npy` with:
- **2814 samples** total from all directions:
  - 712 backward samples (25.3%)
  - 690 forward samples (24.5%)
  - 702 left samples (24.9%)
  - 710 right samples (25.2%)
- **2688 features** per sample
- **4 classes**: 0=backward, 1=forward, 2=left, 3=right
- **Balanced distribution** (~25% per class)

### Data Structure

```python
{
    'features': np.ndarray,  # Shape: (2814, 2688)
    'labels': np.ndarray,    # Shape: (2814,) - values in {0, 1, 2, 3}
    'metadata': pd.DataFrame # 2814 rows with direction labels
}
```

### Label Mapping

| Class | Direction | Sample Count | Percentage |
|-------|-----------|--------------|------------|
| 0     | backward  | 712          | 25.3%      |
| 1     | forward   | 690          | 24.5%      |
| 2     | left      | 702          | 24.9%      |
| 3     | right     | 710          | 25.2%      |

### Use Cases

**✓ Recommended for Classification**

Multiclass mode is the standard choice for:
1. **Direction classification**: Train models to predict movement direction
2. **Model comparison**: Compare different algorithms on the same task
3. **Real-world application**: Mimics actual BCI scenarios
4. **Balanced learning**: Classes are well-balanced for fair training

**✓ When to Use**

Use multiclass mode when:
- Training supervised classification models
- Comparing model performance
- Building a direction prediction system
- Evaluating preprocessing techniques on classification accuracy
- Following standard ML best practices

### Example Configuration

```yaml
Data:
  source: data/
  # Will load directions_multiclass.npy
  feature_key: features
  target_key: labels
  split:
    train: 0.7
    val: 0.15
    test: 0.15
    stratify: true  # Important for balanced splits

Models:
  - name: LogisticRegression
    params:
      max_iter: 1000
      multi_class: multinomial  # For 4-class problem
      
  - name: RandomForest
    params:
      n_estimators: 100
```

---

## Detailed Comparison

### Data Preparation Process

#### Forward-Only Mode

```
Step 1: Load forward data
  └─ recorded_data_forward_20251110_130851.npy
     └─ Shape: (690, 192, 14)

Step 2: Flatten (690, 192, 14) → (690, 2688)

Step 3: Create labels
  └─ All 690 samples labeled as 1

Step 4: Create metadata
  └─ Direction: 'forward' for all

Step 5: Save to forward_prepared.npy
```

#### Multiclass Mode

```
Step 1: Load all directions
  ├─ recorded_data_backward_*.npy  → 712 samples → label 0
  ├─ recorded_data_forward_*.npy   → 690 samples → label 1
  ├─ recorded_data_left_*.npy      → 702 samples → label 2
  └─ recorded_data_right_*.npy     → 710 samples → label 3

Step 2: Flatten each
  └─ (n, 192, 14) → (n, 2688) per direction

Step 3: Concatenate
  └─ Vertical stack: 712 + 690 + 702 + 710 = 2814 samples

Step 4: Create unified labels
  └─ Labels: [0, 0, ..., 1, 1, ..., 2, 2, ..., 3, 3, ...]

Step 5: Save to directions_multiclass.npy
```

### Feature Space

Both modes produce the same feature dimensionality:

```
Original shape per sample: (192 timesteps, 14 channels)
Flattened shape: 192 × 14 = 2688 features

Feature vector contains:
  - Timestep 0: [ch0, ch1, ch2, ..., ch13]  (14 values)
  - Timestep 1: [ch0, ch1, ch2, ..., ch13]  (14 values)
  - ...
  - Timestep 191: [ch0, ch1, ch2, ..., ch13]  (14 values)
Total: 192 × 14 = 2688 features
```

### Memory Requirements

| Mode         | Samples | Features | Memory (float64) |
|--------------|---------|----------|------------------|
| Forward-only | 690     | 2688     | ~14 MB           |
| Multiclass   | 2814    | 2688     | ~57 MB           |

### Training Time (Approximate)

On a typical laptop (based on complexity):

| Model               | Forward-Only | Multiclass |
|---------------------|--------------|------------|
| Logistic Regression | 1-2 sec      | 5-10 sec   |
| Decision Tree       | < 1 sec      | 2-3 sec    |
| SVM (RBF kernel)    | 5-10 sec     | 30-60 sec  |
| Random Forest       | 2-5 sec      | 10-20 sec  |

### Evaluation Metrics

#### Forward-Only Mode

❌ **Problematic metrics** (all samples same class):
- Accuracy: Always 100% (meaningless)
- Precision/Recall: Undefined or 100%
- F1-Score: Meaningless
- Confusion Matrix: Single cell

#### Multiclass Mode

✓ **Meaningful metrics**:
- Accuracy: Proportion of correct predictions
- Precision: Per-class and weighted average
- Recall: Per-class and weighted average
- F1-Score: Harmonic mean of precision/recall
- Confusion Matrix: 4×4 matrix showing all predictions

---

## Workflow Examples

### Example 1: Standard Classification Pipeline (Multiclass)

```bash
# 1. Prepare multiclass data
poetry run python prepare_direction_data.py --mode multiclass

# 2. Run pipeline with default config
poetry run python run_forward_pipeline.py

# 3. View results
xdg-open results/forward_direction/results.html
```

**Expected Output:**
- Trained models on 4-class problem
- Accuracy typically 60-90% depending on model
- Confusion matrix showing inter-class confusion
- Best model recommendations

### Example 2: Feature Analysis (Forward-Only)

```bash
# 1. Prepare forward-only data
poetry run python prepare_direction_data.py --mode forward-only

# 2. Extract and analyze features
python -c "
import numpy as np
data = np.load('data/forward_prepared.npy', allow_pickle=True).item()
X = data['features']
print(f'Mean per channel: {X.reshape(-1, 192, 14).mean(axis=(0,1))}')
print(f'Std per channel: {X.reshape(-1, 192, 14).std(axis=(0,1))}')
"
```

**Use Case:** Understanding forward-specific signal characteristics

---

## Recommendations

### ✅ Use Multiclass Mode When:
- Training classification models
- Comparing model performance
- Building a production system
- Following ML best practices
- You need meaningful evaluation metrics

### ⚠️ Use Forward-Only Mode When:
- Analyzing forward-specific patterns
- Testing preprocessing on single class
- Anomaly detection setups
- Feature engineering experiments
- You understand the limitations

### 🚫 Don't Use Forward-Only Mode For:
- Standard supervised learning
- Model comparison benchmarks
- Production classification systems
- Reporting accuracy metrics

---

## Converting Between Modes

You can prepare both datasets simultaneously:

```bash
# Prepare both
poetry run python prepare_direction_data.py --mode forward-only
poetry run python prepare_direction_data.py --mode multiclass

# Files created:
# - data/forward_prepared.npy (690 samples, 1 class)
# - data/directions_multiclass.npy (2814 samples, 4 classes)
```

Then switch by modifying your config:

```yaml
Data:
  source: data/
  # For multiclass:
  # Will load directions_multiclass.npy
  
  # For forward-only:
  # Will load forward_prepared.npy
```

---

## Technical Details

### File Format

Both modes produce the same file structure (Python dictionary saved with `np.save`):

```python
{
    'features': np.ndarray,   # float64 array
    'labels': np.ndarray,     # int array
    'metadata': pd.DataFrame  # pandas DataFrame
}
```

### Loading the Data

```python
import numpy as np

# Load prepared data
data = np.load('data/directions_multiclass.npy', allow_pickle=True).item()

X = data['features']  # Feature matrix
y = data['labels']    # Label array
metadata = data['metadata']  # Metadata DataFrame

print(f"Samples: {len(X)}")
print(f"Features: {X.shape[1]}")
print(f"Classes: {len(np.unique(y))}")
```

### Integration with Modulus Pipeline

The modulus framework automatically detects and loads the prepared data through the `NpyDataLoader`:

```python
from modulus.infrastructure.loaders.npy_loader import NpyDataLoader

loader = NpyDataLoader(
    data_dir='data/',
    feature_key='features',
    target_key='labels',
    metadata_key='metadata'
)

dataset = loader.load()  # Loads .npy files from directory
```

---

## Summary

| Aspect                  | Forward-Only         | Multiclass          |
|-------------------------|----------------------|---------------------|
| **Samples**             | 690                  | 2814                |
| **Classes**             | 1 (all forward)      | 4 (balanced)        |
| **Classification**      | ❌ Not suitable      | ✅ Standard approach |
| **Evaluation Metrics**  | ❌ Meaningless       | ✅ Meaningful       |
| **Training Time**       | Fast                 | Moderate            |
| **Memory**              | ~14 MB               | ~57 MB              |
| **Use Case**            | Analysis, features   | Classification      |
| **Recommended**         | Special cases only   | ✅ Yes              |

**Bottom Line**: Use **multiclass mode** for all standard classification tasks. Use forward-only mode only for specialized analysis or anomaly detection scenarios.

