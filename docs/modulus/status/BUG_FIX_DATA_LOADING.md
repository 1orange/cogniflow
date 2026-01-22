# 🐛 Bug Fix: Data Loading Issue in Experiments

## Problem Discovered

Both `binary` and `multiclass` experiments were producing **IDENTICAL results**:
- Same accuracy: 73.73%
- Same F1-score: 0.6594
- Same ROC-AUC: 0.8767
- Exact same top 10 configurations

This was **WRONG** - they should have different results since they're solving different problems!

## Root Cause

`NpyDataLoader` was loading **ALL** `.npy` files in `data/prepared/` directory and concatenating them:

```python
# Old buggy code (line 49 of npy_loader.py)
npy_files = sorted(self.data_dir.glob("*.npy"))  # Loads ALL files!
```

So when running experiments, it loaded:
1. `forward_vs_rest_binary.npy` (binary, 2814 samples)
2. `directions_multiclass.npy` (multiclass, 2814 samples)
3. `forward_prepared.npy` (single class, 690 samples)

**Total**: 8,238 samples (mixed data!) 😱

## The Fix

### 1. Updated `NpyDataLoader` to support specific file loading

**File**: `modulus/infrastructure/loaders/npy_loader.py`

Changes:
- Added `specific_file` parameter to `__init__`
- If `data_dir` is a file path, extract filename and directory
- Only load the specific file if provided

```python
def __init__(
    self,
    data_dir: str,
    specific_file: Optional[str] = None,  # NEW parameter
    ...
):
    self.specific_file = specific_file
    
    # If data_dir is actually a file, extract directory and filename
    if self.data_dir.is_file():
        self.specific_file = self.data_dir.name
        self.data_dir = self.data_dir.parent

def load(self) -> Dataset:
    # Load specific file if specified, otherwise load all
    if self.specific_file:
        npy_files = [self.data_dir / self.specific_file]
    else:
        npy_files = sorted(self.data_dir.glob("*.npy"))
```

### 2. Updated `run_preprocessing_experiments.py` to pass specific file

**File**: `run_preprocessing_experiments.py` (line ~72)

Changed from:
```python
self.data_loader = NpyDataLoader(
    data_dir=data_path,  # Directory - loads ALL files!
    ...
)
```

To:
```python
self.data_loader = NpyDataLoader(
    data_dir=str(full_path),  # Specific file path!
    ...
)
```

Where `full_path` is:
- `data/prepared/forward_vs_rest_binary.npy` for binary mode
- `data/prepared/directions_multiclass.npy` for multiclass mode

## Verification

Tested that each mode now loads the correct data:

```bash
✅ BINARY mode:
  - Loaded: 2814 samples
  - Labels: {0, 1}
  - Distribution: {0: 2124 (not-forward), 1: 690 (forward)}

✅ MULTICLASS mode:
  - Loaded: 2814 samples
  - Labels: {0, 1, 2, 3}
  - Distribution: {0: 712 (backward), 1: 690 (forward), 
                   2: 702 (left), 3: 710 (right)}
```

**These are now DIFFERENT as expected!** ✅

## Impact on Results

### Old (Buggy) Results
- Binary and multiclass had IDENTICAL results
- Best accuracy: 73.73% (None + SVM)
- Actually trained on 8,238 mixed samples

### New (Correct) Results
- Binary and multiclass will have DIFFERENT results
- Each trained on correct 2814 samples
- Results will reflect actual task difficulty:
  - Binary: Easier (2 classes: forward vs not-forward)
  - Multiclass: Harder (4 classes: distinguish all directions)

### Expected Changes

**Binary Classification** (forward vs not-forward):
- **Likely HIGHER accuracy** (simpler task)
- Expected: 75-85%+
- Better F1-score on minority class (forward)

**Multiclass Classification** (4 directions):
- **Likely LOWER accuracy** (harder task)
- Expected: 60-75%
- More confusion between similar directions

## Next Steps

### ⚠️ YOU MUST RE-RUN THE EXPERIMENTS ⚠️

Previous results are **INVALID**. Re-run to get correct results:

```bash
# 1. Clean old results (optional)
rm -rf results/experiments_binary/
rm -rf results/experiments_multiclass/

# 2. Run binary experiments
poetry run python run_preprocessing_experiments.py --mode binary --quick

# 3. Run multiclass experiments
poetry run python run_preprocessing_experiments.py --mode multiclass --quick

# 4. Compare the NEW results
cat results/experiments_binary/best_configurations_*.txt
cat results/experiments_multiclass/best_configurations_*.txt
```

### What to Look For

Now you should see:
1. **Different accuracy** between binary and multiclass
2. **Binary should be easier** (higher accuracy expected)
3. **Multiclass should be harder** (lower accuracy expected)
4. **Different best configurations** may emerge for each task
5. **EEG preprocessing impact** will be clearer

## Files Modified

1. `modulus/infrastructure/loaders/npy_loader.py`
   - Added `specific_file` parameter
   - Added file path handling
   - Updated `load()` method

2. `run_preprocessing_experiments.py`
   - Changed to pass specific file path instead of directory

## Backward Compatibility

✅ **Old code still works!**

If you don't specify a file and just pass a directory, it will still load all files (old behavior):

```python
# Still works - loads ALL files in directory
loader = NpyDataLoader(data_dir="data/prepared/")

# New way - loads SPECIFIC file
loader = NpyDataLoader(data_dir="data/prepared/forward_vs_rest_binary.npy")
```

---

## Summary

✅ Bug identified and fixed
✅ Loader now supports specific file loading
✅ Experiments will now use correct data
✅ Backward compatible

⚠️ **ACTION REQUIRED**: Re-run experiments to get valid results!

```bash
poetry run python run_preprocessing_experiments.py --mode binary --quick
poetry run python run_preprocessing_experiments.py --mode multiclass --quick
```

