# Custom Preprocessing Guide

This guide shows you how to add your own preprocessing techniques to the modulus framework while following the Clean Architecture principles defined in the SDD.

## Quick Start

### 1. Prepare Your Data

First, convert your raw .npy files into the format expected by modulus:

```bash
# For multi-class direction classification (recommended)
poetry run python prepare_direction_data.py --mode multiclass

# Or for forward-only (all samples labeled as class 1)
poetry run python prepare_direction_data.py --mode forward-only
```

This creates `data/directions_multiclass.npy` with:
- **Features**: Flattened time-series data (n_samples, 2688 features)
- **Labels**: Direction labels (0=backward, 1=forward, 2=left, 3=right)
- **Metadata**: Sample information (sample_id, direction, window_index)

### 2. Run the Pipeline

```bash
poetry run python run_forward_pipeline.py
```

This will:
1. Load the prepared data
2. Split into train/val/test sets (70/15/15)
3. Apply preprocessing (scaling + PCA)
4. Train 4 models: Logistic Regression, Decision Tree, SVM, Random Forest
5. Evaluate and compare results
6. Generate reports in `results/forward_direction/`

## Adding Custom Preprocessing Techniques

### Method 1: Use Existing Custom Transformers

The framework provides several custom preprocessing transformers in `modulus/application/custom_preprocessing.py`:

#### 1. TimeSeriesFeatureExtractor
Extract statistical features from time-series data:

```yaml
# config/forward_direction_config.yaml
Preprocessing:
  extract_features: true
  feature_list:
    - mean      # Mean value per channel
    - std       # Standard deviation per channel
    - energy    # Energy (sum of squares) per channel
    - range     # Range (max-min) per channel
    - min       # Minimum value per channel
    - max       # Maximum value per channel
    - variance  # Variance per channel
```

**Effect**: Converts (n_samples, 192×14=2688) → (n_samples, 4×14=56) features

#### 2. MovingAverageFilter
Smooth signals with moving average:

```yaml
Preprocessing:
  moving_average: true
  moving_average_window: 5  # Window size for smoothing
```

**Effect**: Reduces noise in time-series signals

#### 3. ChannelSelector
Select specific EEG channels:

```yaml
Preprocessing:
  selected_channels: [0, 1, 2, 3, 4]  # Keep first 5 channels
```

**Effect**: Converts (n_samples, 192×14) → (n_samples, 192×5) features

#### 4. DimensionalityReducer
Downsample the time axis:

```yaml
Preprocessing:
  downsample_factor: 2  # Keep every 2nd timestep
```

**Effect**: Converts (n_samples, 192×14) → (n_samples, 96×14) features

#### 5. RobustScaler
Scale using median and IQR (more robust to outliers):

```yaml
Preprocessing:
  robust_scaler: true  # Instead of standard_scaler
  standard_scaler: false
```

### Method 2: Create Your Own Preprocessing Transformer

Follow the sklearn transformer interface:

```python
# modulus/application/custom_preprocessing.py

from sklearn.base import BaseEstimator, TransformerMixin
import numpy as np

class MyCustomTransformer(BaseEstimator, TransformerMixin):
    """Your custom preprocessing technique."""
    
    def __init__(self, param1=10, param2='default'):
        """Initialize with your parameters."""
        self.param1 = param1
        self.param2 = param2
    
    def fit(self, X, y=None):
        """Learn parameters from training data (if needed)."""
        # Example: compute and store training statistics
        self.mean_ = np.mean(X, axis=0)
        return self
    
    def transform(self, X):
        """Apply transformation to data."""
        # Your preprocessing logic here
        X_transformed = X - self.mean_  # Example
        return X_transformed
```

Then add it to `ExtendedPreprocessingManager`:

```python
# modulus/application/extended_preprocessing_manager.py

from modulus.application.custom_preprocessing import MyCustomTransformer

class ExtendedPreprocessingManager:
    def build(self, X: Optional[np.ndarray] = None) -> Pipeline:
        steps = []
        
        # ... existing steps ...
        
        # Add your custom transformer
        if self.config.get("use_my_custom", False):
            steps.append((
                "my_custom",
                MyCustomTransformer(
                    param1=self.config.get("my_custom_param1", 10),
                    param2=self.config.get("my_custom_param2", 'default'),
                )
            ))
        
        # ... rest of pipeline ...
```

Update your config:

```yaml
Preprocessing:
  use_my_custom: true
  my_custom_param1: 20
  my_custom_param2: 'custom_value'
```

## Example Configurations

### Configuration 1: Feature Extraction + PCA

Best for: Reducing dimensionality while preserving information

```yaml
Preprocessing:
  # Extract statistical features (2688 → 56 features)
  extract_features: true
  feature_list:
    - mean
    - std
    - energy
    - range
  
  # Scale features
  standard_scaler: true
  
  # Further reduce with PCA
  pca_components: 20
```

### Configuration 2: Downsampling + Smoothing

Best for: Noisy high-frequency data

```yaml
Preprocessing:
  # Reduce time resolution (192 → 96 timesteps)
  downsample_factor: 2
  
  # Smooth signals
  moving_average: true
  moving_average_window: 5
  
  # Scale and reduce
  standard_scaler: true
  pca_components: 100
```

### Configuration 3: Channel Selection + Robust Scaling

Best for: When you know which channels are important

```yaml
Preprocessing:
  # Select specific channels
  selected_channels: [0, 1, 2, 5, 7, 9]  # 6 channels
  
  # Robust scaling (better for outliers)
  robust_scaler: true
  
  # PCA for final reduction
  pca_components: 50
```

### Configuration 4: Minimal Preprocessing (Fast)

Best for: Quick experiments

```yaml
Preprocessing:
  # Just downsample heavily and scale
  downsample_factor: 4  # 192 → 48 timesteps
  standard_scaler: true
  pca_components: 50
```

## Complete Example Workflow

```bash
# 1. Prepare data
poetry run python prepare_forward_data.py --mode multiclass

# 2. Edit config with your custom preprocessing
nano config/forward_direction_config.yaml

# 3. Run pipeline
poetry run python run_forward_pipeline.py

# 4. View results
xdg-open results/forward_direction/results.html
```

## Architecture Integration (per SDD)

Your custom preprocessing follows the Clean Architecture layers:

```
┌─────────────────────────────────────────────────────────┐
│  Application Layer                                      │
│  ┌───────────────────────────────────────────────────┐ │
│  │ ExtendedPreprocessingManager                      │ │
│  │   - Orchestrates preprocessing pipeline          │ │
│  │   - Follows domain protocols                      │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                          │
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Infrastructure Layer                                   │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Custom Preprocessing Transformers                 │ │
│  │   - TimeSeriesFeatureExtractor                    │ │
│  │   - MovingAverageFilter                           │ │
│  │   - ChannelSelector                               │ │
│  │   - YourCustomTransformer                         │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Key Principles:

1. **Separation of Concerns**: Preprocessing logic is separate from business logic
2. **Dependency Inversion**: PreprocessingManager depends on abstractions (sklearn interface)
3. **Open/Closed**: Extend with new transformers without modifying core code
4. **Single Responsibility**: Each transformer does one thing well

## Testing Your Custom Preprocessing

```python
# test_custom_preprocessing.py
import numpy as np
from modulus.application.custom_preprocessing import MyCustomTransformer

def test_my_custom_transformer():
    # Create test data
    X_train = np.random.randn(100, 2688)
    X_test = np.random.randn(20, 2688)
    
    # Create and fit transformer
    transformer = MyCustomTransformer(param1=15)
    transformer.fit(X_train)
    
    # Transform data
    X_train_transformed = transformer.transform(X_train)
    X_test_transformed = transformer.transform(X_test)
    
    # Verify output shape and properties
    assert X_train_transformed.shape == X_train.shape
    print("✓ Custom transformer works!")

if __name__ == "__main__":
    test_my_custom_transformer()
```

## Troubleshooting

### Issue: "Pipeline not built or fitted"

**Solution**: Ensure you call `build()` or `fit()` before `transform()`:

```python
preprocessing_manager.fit(X_train)
X_transformed = preprocessing_manager.transform(X_test)
```

### Issue: Shape mismatch after custom preprocessing

**Solution**: Ensure your transformer returns the correct shape. Use prints for debugging:

```python
def transform(self, X):
    print(f"Input shape: {X.shape}")
    X_transformed = your_transformation(X)
    print(f"Output shape: {X_transformed.shape}")
    return X_transformed
```

### Issue: Custom config parameters not recognized

**Solution**: Make sure you:
1. Add parameters to config YAML
2. Read them in `ExtendedPreprocessingManager.build()`
3. Pass them to your transformer's `__init__()`

## Next Steps

1. **Experiment with combinations**: Try different preprocessing pipelines
2. **Measure impact**: Compare accuracy with/without each technique
3. **Optimize**: Find the best preprocessing for your specific data
4. **Document**: Add comments explaining why you chose specific techniques

## Resources

- **SDD.md**: System architecture and design principles
- **modulus/application/custom_preprocessing.py**: Custom transformer implementations
- **modulus/application/extended_preprocessing_manager.py**: Integration logic
- **config/forward_direction_config.yaml**: Example configuration

