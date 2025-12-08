# Modulus ML Pipeline - Documentation Index

Complete documentation for the Modulus ML Pipeline framework.

## 📚 Documentation Structure

### 🚀 Getting Started (Start Here!)

1. **[Quick Start Guide](quick-start.md)**
   - 5-minute setup and first run
   - Basic workflow
   - Common commands
   - **Start here if you're new!**

2. **[Preprocessing Modes](preprocessing-modes.md)** ⭐
   - Forward-only vs Multiclass explained
   - When to use each mode
   - Detailed comparison
   - **Important: Understand the difference!**

3. **[Adding Custom Preprocessing](adding-custom-preprocessing.md)** ⭐
   - Where to put your code
   - Step-by-step integration
   - Complete examples
   - **Essential for custom techniques!**

### 📖 Core Documentation

4. **[Custom Preprocessing Guide](custom-preprocessing.md)**
   - Available custom transformers
   - Configuration examples
   - Best practices
   - Use cases

5. **[Preprocessing Experiments](preprocessing-experiments.md)** ⭐ NEW!
   - Automated testing of all combinations
   - Find optimal preprocessing + model
   - Comprehensive comparison
   - Scientific methodology

6. **[System Design Document (SDD)](../SDD.md)**
   - Clean Architecture overview
   - Component design
   - Data flow
   - Design principles

### 📁 Project Files

```
modulus/
├── docs/                          ← YOU ARE HERE
│   ├── INDEX.md                   ← This file
│   ├── README.md                  ← Documentation overview
│   ├── quick-start.md             ← Start here
│   ├── preprocessing-modes.md     ← Forward-only vs multiclass
│   ├── adding-custom-preprocessing.md  ← Where to put custom code
│   └── custom-preprocessing.md    ← Custom preprocessing guide
│
├── modulus/                       ← Core framework code
│   ├── application/
│   │   ├── custom_preprocessing.py      ← PUT YOUR TRANSFORMERS HERE
│   │   ├── extended_preprocessing_manager.py  ← REGISTER THEM HERE
│   │   ├── data_manager.py
│   │   ├── trainer.py
│   │   └── ...
│   ├── domain/
│   │   ├── entities.py
│   │   └── protocols.py
│   └── infrastructure/
│       ├── loaders/
│       └── ml/
│
├── config/                        ← Configuration files
│   ├── forward_direction_config.yaml  ← Main config (CONFIGURE HERE)
│   ├── example_config.yaml
│   └── advanced_config.yaml
│
├── data/                          ← Data directory
│   ├── recorded_data_forward_*.npy    ← Raw data
│   ├── forward_prepared.npy           ← Prepared (forward-only)
│   └── directions_multiclass.npy      ← Prepared (multiclass)
│
├── prepare_direction_data.py      ← Data preparation script
├── run_forward_pipeline.py        ← Main pipeline script
├── train_compare_models.py        ← Standalone training script
└── SDD.md                         ← System design document
```

## 🎯 Quick Navigation

### I want to...

#### ...run the pipeline quickly
→ Go to [Quick Start Guide](quick-start.md)

#### ...understand forward-only vs multiclass
→ Go to [Preprocessing Modes](preprocessing-modes.md)

#### ...add my own preprocessing function
→ Go to [Adding Custom Preprocessing](adding-custom-preprocessing.md)

#### ...see available preprocessing options
→ Go to [Custom Preprocessing Guide](custom-preprocessing.md)

#### ...find the best preprocessing + model combination
→ Go to [Preprocessing Experiments](preprocessing-experiments.md) ⭐

#### ...understand the architecture
→ Go to [SDD.md](../SDD.md)

#### ...configure the pipeline
→ Edit [config/forward_direction_config.yaml](../config/forward_direction_config.yaml)

#### ...see example code
→ Check [modulus/application/custom_preprocessing.py](../modulus/application/custom_preprocessing.py)

## 📝 Key Concepts

### Data Preparation Modes

| Mode | File | Samples | Classes | Use Case |
|------|------|---------|---------|----------|
| **multiclass** | `directions_multiclass.npy` | 2814 | 4 | ✅ Standard classification |
| **forward-only** | `forward_prepared.npy` | 690 | 1 | Analysis only |

**→ See [Preprocessing Modes](preprocessing-modes.md) for details**

### Custom Preprocessing Locations

| What | Where | Why |
|------|-------|-----|
| **Transformer class** | `modulus/application/custom_preprocessing.py` | Infrastructure layer |
| **Integration** | `modulus/application/extended_preprocessing_manager.py` | Application layer |
| **Configuration** | `config/*.yaml` | External config |

**→ See [Adding Custom Preprocessing](adding-custom-preprocessing.md) for step-by-step guide**

### Available Custom Transformers

1. **TimeSeriesFeatureExtractor** - Extract statistical features (mean, std, energy, etc.)
2. **MovingAverageFilter** - Smooth signals with moving average
3. **ChannelSelector** - Select specific EEG channels
4. **DimensionalityReducer** - Downsample time axis
5. **RobustScaler** - Scale using median/IQR (robust to outliers)
6. **YourCustomTransformer** - Add your own!

**→ See [Custom Preprocessing Guide](custom-preprocessing.md) for usage examples**

## 🔄 Typical Workflows

### Workflow 1: Standard Classification

```bash
# 1. Prepare multiclass data
poetry run python prepare_direction_data.py --mode multiclass

# 2. Run pipeline
poetry run python run_forward_pipeline.py

# 3. View results
xdg-open results/forward_direction/results.html
```

### Workflow 2: Custom Preprocessing

```bash
# 1. Add transformer to custom_preprocessing.py
nano modulus/application/custom_preprocessing.py

# 2. Register in extended_preprocessing_manager.py
nano modulus/application/extended_preprocessing_manager.py

# 3. Configure in YAML
nano config/forward_direction_config.yaml

# 4. Run pipeline
poetry run python run_forward_pipeline.py
```

### Workflow 3: Experiment with Different Preprocessing

```bash
# 1. Edit config
nano config/forward_direction_config.yaml

# 2. Try feature extraction
# Set: extract_features: true

# 3. Run
poetry run python run_forward_pipeline.py

# 4. Compare results
cat results/forward_direction/summary.txt

# 5. Try different settings
# Set: pca_components: 50
# Set: downsample_factor: 2

# 6. Run again and compare
poetry run python run_forward_pipeline.py
```

## 📊 Configuration Examples

### Basic Configuration

```yaml
Preprocessing:
  standard_scaler: true
  pca_components: 100

Models:
  - name: LogisticRegression
  - name: DecisionTree
  - name: SVM
  - name: RandomForest
```

### With Custom Preprocessing

```yaml
Preprocessing:
  # Apply moving average smoothing
  moving_average: true
  moving_average_window: 5
  
  # Extract statistical features
  extract_features: true
  feature_list:
    - mean
    - std
    - energy
  
  # Scale and reduce
  standard_scaler: true
  pca_components: 50
```

### Advanced Configuration

```yaml
Preprocessing:
  # Downsample to reduce dimensions
  downsample_factor: 2
  
  # Select specific channels
  selected_channels: [0, 1, 2, 5, 7, 9]
  
  # Apply robust scaling
  robust_scaler: true
  
  # PCA with variance retention
  pca_components: 0.95  # Keep 95% variance
```

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────┐
│  Configuration (YAML)               │  ← External config
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│  Pipeline Runner                    │  ← Application Layer
│  - Orchestrates workflow            │
│  - Coordinates components           │
└──────────────┬──────────────────────┘
               │
       ┌───────┼───────┬───────────┐
       ↓       ↓       ↓           ↓
   ┌──────┐ ┌────┐ ┌────────┐ ┌────────┐
   │ Data │ │Pre │ │Trainer │ │Report  │
   │ Mgr  │ │Proc│ │        │ │Manager │
   └──┬───┘ └──┬─┘ └───┬────┘ └────┬───┘
      │        │       │           │
      ↓        ↓       ↓           ↓
   ┌───────────────────────────────────┐
   │  Infrastructure Layer             │  ← Custom transformers here
   │  - NpyDataLoader                  │
   │  - TimeSeriesFeatureExtractor     │
   │  - YourCustomTransformer          │
   └───────────────────────────────────┘
```

**→ See [SDD.md](../SDD.md) for detailed architecture**

## 🔧 Common Tasks

### Add a New Preprocessing Technique

1. Create transformer class in `modulus/application/custom_preprocessing.py`
2. Import and register in `modulus/application/extended_preprocessing_manager.py`
3. Add config options to `config/forward_direction_config.yaml`
4. Run pipeline

**→ See [Adding Custom Preprocessing](adding-custom-preprocessing.md)**

### Compare Different Models

1. Edit `Models` section in config
2. Add/remove models as needed
3. Run pipeline
4. Check `results/forward_direction/results.csv`

### Try Different Feature Engineering

1. Edit `Preprocessing` section in config
2. Enable/disable different techniques
3. Run pipeline multiple times
4. Compare accuracy in results

### Use Your Own Data

1. Place `.npy` files in `data/` directory
2. Update data dimensions in preprocessing manager
3. Run `prepare_direction_data.py`
4. Run pipeline

## 📞 Support

### Documentation Issues
- Check [Troubleshooting](quick-start.md#troubleshooting) section
- Review [SDD.md](../SDD.md) for architecture details
- Examine example configs in `config/`

### Code Examples
- See `modulus/application/custom_preprocessing.py` for examples
- Check test files in `tests/` directory
- Look at `prepare_direction_data.py` for data handling

### Architecture Questions
- Read [SDD.md](../SDD.md) for Clean Architecture explanation
- Review component responsibilities
- Check dependency flow diagrams

## 🎓 Learning Path

### Beginner
1. [Quick Start Guide](quick-start.md) - Get it running
2. [Preprocessing Modes](preprocessing-modes.md) - Understand your data
3. Run with default config
4. View and interpret results

### Intermediate
1. [Custom Preprocessing Guide](custom-preprocessing.md) - See available options
2. Edit config to try different preprocessing
3. Compare results from different configurations
4. Understand which techniques help

### Advanced
1. [Adding Custom Preprocessing](adding-custom-preprocessing.md) - Create your own
2. [SDD.md](../SDD.md) - Understand architecture
3. Implement custom transformers
4. Extend framework with new components

## 📚 Document Overview

| Document | Purpose | Audience | Estimated Time |
|----------|---------|----------|----------------|
| [quick-start.md](quick-start.md) | Get started quickly | Everyone | 5 min |
| [preprocessing-modes.md](preprocessing-modes.md) | Understand data modes | Everyone | 10 min |
| [adding-custom-preprocessing.md](adding-custom-preprocessing.md) | Add your code | Developers | 15 min |
| [custom-preprocessing.md](custom-preprocessing.md) | Use existing techniques | Users | 20 min |
| [SDD.md](../SDD.md) | Architecture deep-dive | Architects | 30 min |

## 🚀 Next Steps

1. **New user?** → Start with [Quick Start Guide](quick-start.md)
2. **Want to customize?** → Read [Preprocessing Modes](preprocessing-modes.md)
3. **Ready to code?** → Follow [Adding Custom Preprocessing](adding-custom-preprocessing.md)
4. **Need examples?** → Check [Custom Preprocessing Guide](custom-preprocessing.md)
5. **Understanding architecture?** → Read [SDD.md](../SDD.md)

---

**Last Updated**: 2025-11-18  
**Framework Version**: 0.1.0  
**Documentation Status**: Complete

