# Adding Your Own Custom Preprocessing Functions

This guide shows you exactly where to put your custom preprocessing functions and how to integrate them into the Modulus framework following Clean Architecture principles.

## Quick Answer

**Put your custom preprocessing transformers in:**
```
modulus/application/custom_preprocessing.py
```

**Integrate them into the pipeline in:**
```
modulus/application/extended_preprocessing_manager.py
```

**Configure them in:**
```
config/your_config.yaml
```

---

## Step-by-Step Guide

### Step 1: Create Your Custom Transformer

Add your transformer class to `modulus/application/custom_preprocessing.py`:

```python
# modulus/application/custom_preprocessing.py

from sklearn.base import BaseEstimator, TransformerMixin
import numpy as np

class MyCustomPreprocessor(BaseEstimator, TransformerMixin):
    """
    Your custom preprocessing technique.
    
    This transformer does [describe what it does].
    """
    
    def __init__(self, param1=10, param2=0.5):
        """
        Initialize your custom preprocessor.
        
        Args:
            param1: Description of parameter 1
            param2: Description of parameter 2
        """
        self.param1 = param1
        self.param2 = param2
    
    def fit(self, X, y=None):
        """
        Learn any parameters from training data (optional).
        
        Args:
            X: Training feature matrix, shape (n_samples, n_features)
            y: Training labels (optional, usually ignored)
            
        Returns:
            self for method chaining
        """
        # Example: compute statistics from training data
        self.mean_ = np.mean(X, axis=0)
        self.std_ = np.std(X, axis=0)
        
        return self
    
    def transform(self, X):
        """
        Apply your transformation to the data.
        
        Args:
            X: Feature matrix to transform, shape (n_samples, n_features)
            
        Returns:
            Transformed feature matrix
        """
        # Your preprocessing logic here
        X_transformed = (X - self.mean_) / (self.std_ + 1e-8)
        X_transformed *= self.param2
        
        return X_transformed
```

### Step 2: Register Your Transformer

Add your transformer to `modulus/application/extended_preprocessing_manager.py`:

```python
# modulus/application/extended_preprocessing_manager.py

# Add import at the top
from modulus.application.custom_preprocessing import (
    TimeSeriesFeatureExtractor,
    ChannelSelector,
    MovingAverageFilter,
    RobustScaler,
    DimensionalityReducer,
    MyCustomPreprocessor,  # <-- Add your import here
)

class ExtendedPreprocessingManager:
    def build(self, X: Optional[np.ndarray] = None) -> Pipeline:
        steps = []
        
        # ... existing preprocessing steps ...
        
        # Add your custom preprocessing step
        if self.config.get("use_my_custom", False):
            steps.append((
                "my_custom",  # Step name in pipeline
                MyCustomPreprocessor(
                    param1=self.config.get("my_custom_param1", 10),
                    param2=self.config.get("my_custom_param2", 0.5),
                )
            ))
        
        # ... rest of the pipeline ...
```

### Step 3: Configure Your Transformer

Add configuration options to your YAML config file:

```yaml
# config/forward_direction_config.yaml

Preprocessing:
  # ... existing preprocessing options ...
  
  # Your custom preprocessing
  use_my_custom: true
  my_custom_param1: 15
  my_custom_param2: 0.75
```

### Step 4: Run the Pipeline

```bash
poetry run python run_forward_pipeline.py --config config/forward_direction_config.yaml
```

Your custom preprocessing will now be part of the pipeline!

---

## Complete Example: Band-Pass Filter

Here's a complete example of adding a band-pass filter for EEG data:

### 1. Add to `custom_preprocessing.py`

```python
# modulus/application/custom_preprocessing.py

from scipy.signal import butter, filtfilt

class BandPassFilter(BaseEstimator, TransformerMixin):
    """
    Apply band-pass filter to EEG time-series data.
    
    Useful for isolating specific frequency bands (e.g., alpha, beta waves).
    """
    
    def __init__(
        self,
        n_timesteps: int,
        n_channels: int,
        lowcut: float = 8.0,
        highcut: float = 30.0,
        fs: float = 128.0,
        order: int = 4,
    ):
        """
        Initialize band-pass filter.
        
        Args:
            n_timesteps: Number of timesteps in data
            n_channels: Number of channels in data
            lowcut: Low frequency cutoff (Hz)
            highcut: High frequency cutoff (Hz)
            fs: Sampling frequency (Hz)
            order: Filter order
        """
        self.n_timesteps = n_timesteps
        self.n_channels = n_channels
        self.lowcut = lowcut
        self.highcut = highcut
        self.fs = fs
        self.order = order
        
        # Design the filter during initialization
        nyquist = 0.5 * fs
        low = lowcut / nyquist
        high = highcut / nyquist
        self.b, self.a = butter(order, [low, high], btype='band')
    
    def fit(self, X, y=None):
        """Fit transformer (no-op for this filter)."""
        return self
    
    def transform(self, X):
        """
        Apply band-pass filter to data.
        
        Args:
            X: Flattened data, shape (n_samples, n_timesteps * n_channels)
            
        Returns:
            Filtered data with same shape
        """
        n_samples = X.shape[0]
        
        # Reshape to 3D: (n_samples, n_timesteps, n_channels)
        X_reshaped = X.reshape(n_samples, self.n_timesteps, self.n_channels)
        
        # Apply filter to each sample and channel
        X_filtered = np.zeros_like(X_reshaped)
        
        for i in range(n_samples):
            for j in range(self.n_channels):
                X_filtered[i, :, j] = filtfilt(
                    self.b, self.a, X_reshaped[i, :, j]
                )
        
        # Flatten back to 2D
        return X_filtered.reshape(n_samples, -1)
```

### 2. Add to `extended_preprocessing_manager.py`

```python
# modulus/application/extended_preprocessing_manager.py

from modulus.application.custom_preprocessing import (
    # ... existing imports ...
    BandPassFilter,  # <-- Add this
)

class ExtendedPreprocessingManager:
    def build(self, X: Optional[np.ndarray] = None) -> Pipeline:
        steps = []
        
        # ... existing steps ...
        
        # Add band-pass filter (early in pipeline, before feature extraction)
        if self.config.get("bandpass_filter", False):
            if self.n_timesteps and self.n_channels:
                steps.append((
                    "bandpass",
                    BandPassFilter(
                        n_timesteps=self.n_timesteps,
                        n_channels=self.n_channels,
                        lowcut=self.config.get("bandpass_lowcut", 8.0),
                        highcut=self.config.get("bandpass_highcut", 30.0),
                        fs=self.config.get("sampling_rate", 128.0),
                        order=self.config.get("filter_order", 4),
                    )
                ))
        
        # ... rest of pipeline ...
```

### 3. Add to config

```yaml
# config/forward_direction_config.yaml

Preprocessing:
  # Band-pass filter settings
  bandpass_filter: true
  bandpass_lowcut: 8.0   # Low frequency cutoff (Hz)
  bandpass_highcut: 30.0  # High frequency cutoff (Hz)
  sampling_rate: 128.0    # From your metadata
  filter_order: 4
  
  # Other preprocessing
  standard_scaler: true
  pca_components: 100
```

### 4. Run

```bash
poetry run python run_forward_pipeline.py
```

---

## File Structure Overview

```
modulus/
├── application/
│   ├── custom_preprocessing.py          ← PUT YOUR TRANSFORMERS HERE
│   │   ├── TimeSeriesFeatureExtractor
│   │   ├── MovingAverageFilter
│   │   ├── BandPassFilter              ← Your custom transformer
│   │   └── MyCustomPreprocessor        ← Another custom transformer
│   │
│   └── extended_preprocessing_manager.py  ← REGISTER THEM HERE
│       └── ExtendedPreprocessingManager
│           └── build()                 ← Add integration logic
│
├── config/
│   └── forward_direction_config.yaml   ← CONFIGURE THEM HERE
│
└── docs/
    └── adding-custom-preprocessing.md  ← THIS GUIDE
```

---

## Integration Points

### Point 1: Transformer Definition (`custom_preprocessing.py`)

This is the **Infrastructure Layer** in Clean Architecture:
- Contains concrete implementations
- Follows sklearn's transformer interface
- No business logic, just transformations

```python
# Location: modulus/application/custom_preprocessing.py

class YourTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, ...):
        # Initialize parameters
        pass
    
    def fit(self, X, y=None):
        # Learn from training data (optional)
        return self
    
    def transform(self, X):
        # Apply transformation
        return X_transformed
```

### Point 2: Manager Integration (`extended_preprocessing_manager.py`)

This is the **Application Layer** in Clean Architecture:
- Orchestrates transformers
- Reads configuration
- Builds pipelines

```python
# Location: modulus/application/extended_preprocessing_manager.py

class ExtendedPreprocessingManager:
    def build(self, X: Optional[np.ndarray] = None) -> Pipeline:
        steps = []
        
        # Read config and add your transformer
        if self.config.get("use_your_transformer", False):
            steps.append(("your_step", YourTransformer(...)))
        
        return Pipeline(steps)
```

### Point 3: Configuration (`config/*.yaml`)

This is the **Presentation Layer** (external configuration):
- User-facing settings
- No code, just data

```yaml
# Location: config/your_config.yaml

Preprocessing:
  use_your_transformer: true
  your_param: value
```

---

## Best Practices

### 1. Follow sklearn Conventions

✅ **Do:**
```python
class GoodTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, param=10):
        self.param = param  # Store as attribute
    
    def fit(self, X, y=None):
        self.fitted_param_ = compute(X)  # Learned attributes end with _
        return self  # Always return self
    
    def transform(self, X):
        # Use self.fitted_param_
        return transformed_X
```

❌ **Don't:**
```python
class BadTransformer:  # Missing base classes
    def __init__(self, param=10):
        local_var = param  # Not stored as attribute
    
    def fit(self, X):
        pass  # Doesn't return self
    
    def transform(self, X):
        return None  # Returns None instead of transformed data
```

### 2. Handle Shape Changes

If your transformer changes the shape, document it:

```python
class ShapeChanger(BaseEstimator, TransformerMixin):
    """
    Reduces features from 2688 to 100.
    
    Input:  (n_samples, 2688)
    Output: (n_samples, 100)
    """
    
    def transform(self, X):
        # ... reduce dimensionality ...
        return X_reduced  # Shape: (n_samples, 100)
```

### 3. Make It Configurable

```python
class ConfigurableTransformer(BaseEstimator, TransformerMixin):
    def __init__(
        self,
        method='mean',      # Allow different methods
        window_size=5,      # Configurable parameters
        normalize=True,     # Boolean flags
    ):
        self.method = method
        self.window_size = window_size
        self.normalize = normalize
```

### 4. Add Validation

```python
class SafeTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, param=10):
        if param <= 0:
            raise ValueError("param must be positive")
        self.param = param
    
    def fit(self, X, y=None):
        if X.ndim != 2:
            raise ValueError(f"Expected 2D array, got {X.ndim}D")
        return self
```

### 5. Document Everything

```python
class WellDocumented(BaseEstimator, TransformerMixin):
    """
    One-line summary of what this does.
    
    Longer description explaining:
    - When to use this transformer
    - What preprocessing it applies
    - Any assumptions or requirements
    
    Parameters
    ----------
    param1 : int, default=10
        Description of parameter 1
    param2 : float, default=0.5
        Description of parameter 2
    
    Attributes
    ----------
    fitted_value_ : float
        Description of fitted attribute
    
    Examples
    --------
    >>> transformer = WellDocumented(param1=20)
    >>> X_train = np.random.rand(100, 50)
    >>> transformer.fit(X_train)
    >>> X_transformed = transformer.transform(X_train)
    """
```

---

## Common Patterns

### Pattern 1: Time-Series Transformer

For transformers that work on (timesteps, channels) structure:

```python
class TimeSeriesTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, n_timesteps, n_channels):
        self.n_timesteps = n_timesteps
        self.n_channels = n_channels
    
    def transform(self, X):
        # Reshape from flat to 3D
        n_samples = X.shape[0]
        X_3d = X.reshape(n_samples, self.n_timesteps, self.n_channels)
        
        # Apply transformation
        X_transformed = self._process_timeseries(X_3d)
        
        # Reshape back to flat
        return X_transformed.reshape(n_samples, -1)
```

### Pattern 2: Statistical Feature Extractor

For extracting statistical features:

```python
class StatExtractor(BaseEstimator, TransformerMixin):
    def __init__(self, features=['mean', 'std']):
        self.features = features
    
    def transform(self, X):
        extracted = []
        
        for feat in self.features:
            if feat == 'mean':
                extracted.append(np.mean(X, axis=1, keepdims=True))
            elif feat == 'std':
                extracted.append(np.std(X, axis=1, keepdims=True))
        
        return np.hstack(extracted)
```

### Pattern 3: Learnable Transformer

For transformers that learn from training data:

```python
class LearnableTransformer(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        # Learn parameters from training data
        self.mean_ = np.mean(X, axis=0)
        self.std_ = np.std(X, axis=0)
        return self
    
    def transform(self, X):
        # Use learned parameters
        return (X - self.mean_) / (self.std_ + 1e-8)
```

---

## Testing Your Transformer

Create a test file to verify your transformer works:

```python
# test_my_transformer.py

import numpy as np
from modulus.application.custom_preprocessing import MyCustomPreprocessor

def test_my_custom_preprocessor():
    # Create test data
    X_train = np.random.randn(100, 2688)
    X_test = np.random.randn(20, 2688)
    
    # Create transformer
    transformer = MyCustomPreprocessor(param1=15, param2=0.5)
    
    # Fit on training data
    transformer.fit(X_train)
    
    # Transform both sets
    X_train_transformed = transformer.transform(X_train)
    X_test_transformed = transformer.transform(X_test)
    
    # Verify shapes
    assert X_train_transformed.shape == X_train.shape
    assert X_test_transformed.shape == X_test.shape
    
    # Verify no NaN or Inf
    assert not np.any(np.isnan(X_train_transformed))
    assert not np.any(np.isinf(X_train_transformed))
    
    print("✅ All tests passed!")

if __name__ == "__main__":
    test_my_custom_preprocessor()
```

Run with:
```bash
poetry run python test_my_transformer.py
```

---

## Summary

**Where to put your code:**

| What                     | Where                                          | Why                        |
|--------------------------|------------------------------------------------|----------------------------|
| Transformer class        | `modulus/application/custom_preprocessing.py`  | Infrastructure layer       |
| Integration logic        | `modulus/application/extended_preprocessing_manager.py` | Application layer |
| Configuration            | `config/your_config.yaml`                      | External configuration     |
| Tests                    | `tests/unit/test_custom_preprocessing.py`      | Quality assurance          |
| Documentation            | `docs/your-transformer.md`                     | User guidance              |

**Quick checklist:**
- [ ] Add transformer class to `custom_preprocessing.py`
- [ ] Import and integrate in `extended_preprocessing_manager.py`
- [ ] Add configuration options to YAML
- [ ] Test your transformer works
- [ ] Document parameters and usage
- [ ] Run full pipeline to verify integration

That's it! Your custom preprocessing is now part of the Modulus framework following Clean Architecture principles.

