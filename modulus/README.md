# Modulus — ML Pipeline for Cogniflow

> **Part of the [Cogniflow](../README.md) BCI Training System**

Modulus is the integrated machine learning pipeline module for EEG data analysis and model training within Cogniflow. It follows **Clean Architecture** principles and supports reproducible ML workflows.

## Integration with Cogniflow

Modulus is fully integrated with the Cogniflow BCI trainer:

### Using via Pygame Interface (Recommended)

1. Launch Cogniflow: `poetry run python main.py`
2. Press `[M]` to enter the **ML Pipeline (Modulus)** screen
3. Configure experiments using the UI
4. Run training and view results

### Using via CLI (Standalone)

```bash
# From cogniflow root directory
poetry run python -m modulus.cli --config modulus/config/example_config.yaml
```

## Features

- **Clean Architecture**: Separation of concerns with distinct Domain, Application, Infrastructure layers
- **Multiple Data Sources**: Support for `.npy` files with embedded metadata
- **Reproducible Workflows**: Configurable data splitting with seed control
- **Flexible Preprocessing**: Custom and standard preprocessing pipelines
- **Multi-Model Training**: Train and compare multiple models simultaneously
- **Comprehensive Benchmarking**: Automated evaluation with multiple metrics
- **Rich Reporting**: Export results to CSV, JSON, and HTML formats

## Architecture

```
+--------------------------+
|   Presentation Layer     |   <- ModulusScene (Pygame UI) / CLI
+--------------------------+
|   Application Core       |   <- Use Cases (Pipeline Execution)
+--------------------------+
|   Domain                 |   <- Entities (Dataset, ModelConfig)
+--------------------------+
|   Infrastructure / I/O   |   <- Data Access, ML Frameworks
+--------------------------+
```

## Quick Start

### Prerequisites

- Cogniflow installed via poetry (see [main README](../README.md))
- EEG data recorded using the Record scene (or your own `.npy` data)

### Typical Workflow

```bash
# 1. Record EEG data using Cogniflow Record scene
#    Files saved to: data/recorded_data_<direction>_<timestamp>.npy

# 2. Prepare data for ML pipeline
poetry run python modulus/prepare_direction_data.py --mode multiclass

# 3. Run pipeline via CLI
poetry run python -m modulus.cli --config modulus/config/forward_direction_config.yaml

# 4. View results
xdg-open modulus/results/forward_direction/results.html
```

### Using the Pygame Interface

The ModulusScene provides an interactive UI for ML experiments:

- `[UP]/[DOWN]` — Select experiment mode (Binary/Multiclass/Both)
- `[Q]` — Toggle Quick Mode (faster, fewer iterations)
- `[H]` — Toggle Hyperparameter Tuning
- `[ENTER]` — Run experiments
- `[ESC]` — Return to menu

Results are saved to:
- `results/experiments_{mode}_{timestamp}/` — Experiment outputs
- `models/` — Trained model files (`.pkl`)

## Configuration

Configuration files are in `modulus/config/`:

```yaml
Data:
  source: "data/"
  loader: "npy"
  feature_key: "features"
  target_key: "labels"
  split:
    train: 0.7
    val: 0.15
    test: 0.15
    random_state: 42

Preprocessing:
  standard_scaler: true
  pca_components: 100

Models:
  - name: "LogisticRegression"
    params:
      max_iter: 1000
  - name: "RandomForest"
    params:
      n_estimators: 100

Output:
  path: "results/"
  formats: ["csv", "json", "html"]
```

## GPU Support (Optional)

GPU acceleration via cuML/CuPy is optional and falls back to CPU if unavailable:

```bash
# Install with GPU support
poetry install -E gpu

# Run with GPU
poetry run python -m modulus.cli --config config.yaml --use-gpu
```

## Project Structure

```
modulus/
├── modulus/                 # Core ML pipeline framework
│   ├── domain/              # Domain entities and protocols
│   ├── application/         # Use cases and business logic
│   ├── infrastructure/      # Data loaders, ML adapters, storage
│   ├── config.py            # Configuration handling
│   └── container.py         # Dependency injection
├── config/                  # Pipeline configuration files
├── docs/                    # ML pipeline documentation
├── tests/                   # ML pipeline tests
├── prepare_direction_data.py  # Data preparation script
└── run_forward_pipeline.py    # Standalone pipeline runner
```

## Documentation

- **[Documentation Index](docs/INDEX.md)** — Complete docs overview
- **[Quick Start](docs/quick-start.md)** — Get started guide
- **[Preprocessing Modes](docs/preprocessing-modes.md)** — Forward-only vs multiclass
- **[Custom Preprocessing](docs/custom-preprocessing.md)** — Add your own techniques
- **[System Design (SDD)](SDD.md)** — Architecture deep-dive

## Testing

```bash
# Run from cogniflow root
cd modulus
poetry run pytest

# With coverage
poetry run pytest --cov=modulus --cov-report=html
```

## See Also

- [Cogniflow Main README](../README.md) — Full project documentation
- [ModulusScene](../trainer/scenes/modulus.py) — Pygame integration
- [Experiment Features](../docs/modulus/EXPERIMENT_FEATURES.md) — UI experiment guide

## License

Part of the Cogniflow project. See [main README](../README.md) for license information.
