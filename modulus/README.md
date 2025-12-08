# Modular Machine Learning Pipeline (Clean Architecture Edition)

A production-ready, modular ML pipeline built using **Clean Code Architecture** principles. Supports datasets stored as multiple `.npy` files with embedded metadata, reproducible data splitting, preprocessing, multi-model training, and benchmarking.

## Features

- **Clean Architecture**: Separation of concerns with distinct Domain, Application, Infrastructure, and Presentation layers
- **Multiple Data Sources**: Support for `.npy` files with embedded metadata
- **Reproducible Workflows**: Configurable data splitting with seed control
- **Flexible Preprocessing**: Custom and standard preprocessing pipelines
- **Multi-Model Training**: Train and compare multiple models simultaneously
- **Comprehensive Benchmarking**: Automated evaluation with multiple metrics
- **Rich Reporting**: Export results to CSV, JSON, and HTML formats

## Architecture

```
+--------------------------+
|        Presentation      |   <- CLI / API Interface Layer
+--------------------------+
|      Application Core    |   <- Use Cases (Pipeline Execution, Reporting)
+--------------------------+
|         Domain           |   <- Entities (Dataset, ModelConfig, Metrics)
+--------------------------+
|   Infrastructure / I/O   |   <- Data Access (npy, CSV, JSON), ML Frameworks
+--------------------------+
```

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

1. **Prepare your data**: Place `.npy` files in a directory (e.g., `data/`)
   - Each file should contain a dictionary with `features`, `labels`, and optional `metadata`

2. **Configure the pipeline**: Create a `config.yaml` file (see `config/example_config.yaml`)

3. **Run the pipeline**:
```bash
python -m modulus.cli --config config.yaml
```

## Configuration Example

```yaml
Data:
  source: "data/"
  loader: "npy"
  feature_key: "features"
  target_key: "labels"
  use_metadata: true
  split:
    train: 0.7
    val: 0.15
    test: 0.15
    random_state: 42

Preprocessing:
  standard_scaler: true
  pca_components: null

Models:
  - name: "LogisticRegression"
    params:
      max_iter: 1000
  - name: "RandomForest"
    params:
      n_estimators: 100
      random_state: 42

Output:
  path: "results/"
  formats: ["csv", "json", "html"]
```

## Project Structure

```
modulus/
├── domain/                 # Domain entities (pure Python, no frameworks)
│   ├── __init__.py
│   ├── entities.py         # Dataset, SplitConfig, ModelSpec, MetricSet
│   └── protocols.py        # Interface definitions
├── application/            # Use cases and business logic
│   ├── __init__.py
│   ├── pipeline_runner.py  # Main orchestrator
│   ├── data_manager.py     # Data loading and splitting
│   ├── preprocessing_manager.py
│   ├── trainer.py          # Model training
│   ├── benchmark_manager.py
│   └── reporting_manager.py
├── infrastructure/         # External framework integrations
│   ├── __init__.py
│   ├── loaders/
│   │   ├── __init__.py
│   │   └── npy_loader.py   # .npy file loading
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── csv_writer.py
│   │   ├── json_writer.py
│   │   └── html_writer.py
│   └── ml/
│       ├── __init__.py
│       └── sklearn_adapter.py
├── presentation/           # User interfaces
│   ├── __init__.py
│   └── cli.py              # Command-line interface
├── container.py            # Dependency injection
├── config.py               # Configuration handling
└── cli.py                  # CLI entry point

tests/                      # Test suite
├── unit/
├── integration/
└── e2e/
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=modulus --cov-report=html

# Run specific test suite
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
```

## Development

### Type Checking
```bash
mypy modulus/
```

### Adding a New Data Source

1. Implement the `IDataLoader` protocol in `infrastructure/loaders/`
2. Register it in the dependency container
3. Update configuration schema

### Adding a New Model

Simply add it to your `config.yaml`:
```yaml
Models:
  - name: "YourModel"
    params:
      param1: value1
```

## Design Principles

- **Dependency Inversion**: High-level modules don't depend on low-level modules
- **Single Responsibility**: Each class has one reason to change
- **Open/Closed**: Open for extension, closed for modification
- **Interface Segregation**: Clients depend only on interfaces they use
- **Dependency Injection**: Dependencies are injected, not created internally

## License

MIT

## Contributing

Contributions are welcome! Please ensure:
- Code follows Clean Architecture principles
- All tests pass
- Type hints are included
- Documentation is updated

