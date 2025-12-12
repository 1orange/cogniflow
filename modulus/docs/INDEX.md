# Modulus ML Pipeline — Documentation Index

> **Part of [Cogniflow](../../README.md)** — Integrated ML pipeline for EEG analysis

Complete documentation for the Modulus ML Pipeline framework.

## 📚 Documentation Structure

### 🚀 Getting Started (Start Here!)

1. **[Quick Start Guide](quick-start.md)**
   - 5-minute setup and first run
   - Basic workflow (CLI and Pygame UI)
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

5. **[Preprocessing Experiments](preprocessing-experiments.md)** ⭐
   - Automated testing of all combinations
   - Find optimal preprocessing + model
   - Comprehensive comparison

6. **[System Design Document (SDD)](../SDD.md)**
   - Clean Architecture overview
   - Component design
   - Data flow
   - Design principles

### 🎮 Cogniflow Integration

7. **[Experiment Features](../../docs/modulus/EXPERIMENT_FEATURES.md)**
   - Using ModulusScene in Pygame UI
   - Split ratio testing
   - Hyperparameter tuning
   - Model persistence

## 📁 Project Structure

```
cogniflow/                         ← Main project root
├── main.py                        ← App entrypoint
├── data/                          ← EEG recordings
├── models/                        ← Trained models
├── results/                       ← Experiment results
├── trainer/
│   └── scenes/
│       └── modulus.py             ← ModulusScene (Pygame UI)
│
└── modulus/                       ← ML Pipeline module
    ├── docs/                      ← YOU ARE HERE
    │   ├── INDEX.md               ← This file
    │   ├── README.md              ← Documentation overview
    │   ├── quick-start.md         ← Get started guide
    │   ├── preprocessing-modes.md ← Forward-only vs multiclass
    │   └── custom-preprocessing.md
    │
    ├── modulus/                   ← Core framework code
    │   ├── application/
    │   │   ├── custom_preprocessing.py      ← Custom transformers
    │   │   ├── extended_preprocessing_manager.py
    │   │   ├── data_manager.py
    │   │   └── trainer.py
    │   ├── domain/
    │   │   ├── entities.py
    │   │   └── protocols.py
    │   └── infrastructure/
    │       ├── loaders/
    │       └── ml/
    │
    ├── config/                    ← Configuration files
    │   ├── forward_direction_config.yaml
    │   └── example_config.yaml
    │
    ├── prepare_direction_data.py  ← Data preparation script
    └── run_forward_pipeline.py    ← Pipeline runner
```

## 🎯 Quick Navigation

### I want to...

#### ...run experiments via Pygame UI
→ Launch `poetry run python main.py` and press `[M]`

#### ...run the pipeline via CLI
→ Go to [Quick Start Guide](quick-start.md)

#### ...understand forward-only vs multiclass
→ Go to [Preprocessing Modes](preprocessing-modes.md)

#### ...add my own preprocessing function
→ Go to [Adding Custom Preprocessing](adding-custom-preprocessing.md)

#### ...see available preprocessing options
→ Go to [Custom Preprocessing Guide](custom-preprocessing.md)

#### ...find the best preprocessing + model combination
→ Go to [Preprocessing Experiments](preprocessing-experiments.md)

#### ...understand the architecture
→ Go to [SDD.md](../SDD.md)

#### ...configure the pipeline
→ Edit [config/forward_direction_config.yaml](../config/forward_direction_config.yaml)

## 📝 Key Concepts

### Data Preparation Modes

| Mode | File | Samples | Classes | Use Case |
|------|------|---------|---------|----------|
| **multiclass** | `directions_multiclass.npy` | 2814 | 4 | ✅ Standard classification |
| **binary** | `forward_vs_rest_binary.npy` | varies | 2 | Forward vs rest |
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

1. **TimeSeriesFeatureExtractor** — Extract statistical features (mean, std, energy, etc.)
2. **MovingAverageFilter** — Smooth signals with moving average
3. **ChannelSelector** — Select specific EEG channels
4. **DimensionalityReducer** — Downsample time axis
5. **RobustScaler** — Scale using median/IQR (robust to outliers)
6. **YourCustomTransformer** — Add your own!

**→ See [Custom Preprocessing Guide](custom-preprocessing.md) for usage examples**

## 🔄 Typical Workflows

### Workflow 1: Via Pygame UI (Easiest)

```bash
# 1. Launch Cogniflow
poetry run python main.py

# 2. Press [M] for ML Pipeline
# 3. Select mode, toggle options
# 4. Press [ENTER] to run
# 5. View results in results/ folder
```

### Workflow 2: Via CLI

```bash
# 1. Prepare multiclass data
cd modulus
poetry run python prepare_direction_data.py --mode multiclass

# 2. Run pipeline
poetry run python run_forward_pipeline.py

# 3. View results
xdg-open results/forward_direction/results.html
```

### Workflow 3: Custom Preprocessing

```bash
# 1. Add transformer to custom_preprocessing.py
nano modulus/modulus/application/custom_preprocessing.py

# 2. Register in extended_preprocessing_manager.py
nano modulus/modulus/application/extended_preprocessing_manager.py

# 3. Configure in YAML
nano modulus/config/forward_direction_config.yaml

# 4. Run pipeline
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
  moving_average: true
  moving_average_window: 5
  extract_features: true
  feature_list:
    - mean
    - std
    - energy
  standard_scaler: true
  pca_components: 50
```

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────┐
│  Cogniflow UI (Pygame)              │  ← ModulusScene
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│  Configuration (YAML)               │  ← External config
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│  Pipeline Runner                    │  ← Application Layer
└──────────────┬──────────────────────┘
               │
       ┌───────┼───────┬───────────┐
       ↓       ↓       ↓           ↓
   ┌──────┐ ┌────┐ ┌────────┐ ┌────────┐
   │ Data │ │Pre │ │Trainer │ │Report  │
   │ Mgr  │ │Proc│ │        │ │Manager │
   └──────┘ └────┘ └────────┘ └────────┘
               │
               ↓
   ┌───────────────────────────────────┐
   │  Infrastructure Layer             │  ← Custom transformers
   └───────────────────────────────────┘
```

**→ See [SDD.md](../SDD.md) for detailed architecture**

## 📞 Related Documentation

### Cogniflow Main Docs
- [Main README](../../README.md) — Full project documentation
- [Emotiv Integration](../../docs/README.md) — BCI hardware docs

### Modulus-Specific
- [Modulus README](../README.md) — Module overview
- [SDD.md](../SDD.md) — System design document
- [Config Examples](../config/) — Configuration files

---

**Last Updated**: 2025-12-12
**Part of**: Cogniflow BCI Training System
**Documentation Status**: Complete
