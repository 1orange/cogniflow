# Modulus ML Pipeline — Documentation

> **Part of [Cogniflow](../../README.md)** — Integrated ML pipeline for EEG analysis

Welcome to the Modulus ML Pipeline documentation. Modulus is the machine learning component of Cogniflow, providing comprehensive tools for EEG data analysis and model training.

## Quick Links

- **[📖 Documentation Index](INDEX.md)** — Full documentation overview
- **[🚀 Quick Start](quick-start.md)** — Get running in 5 minutes
- **[🎮 Pygame Integration](../../docs/modulus/QUICKSTART.md)** — Using via Cogniflow UI

## Documentation Structure

### Getting Started
- **[Quick Start Guide](quick-start.md)** — Get up and running in 5 minutes
- **[Preprocessing Modes](preprocessing-modes.md)** — Understanding forward-only vs multiclass

### Core Concepts
- **[Custom Preprocessing](custom-preprocessing.md)** — Available preprocessing techniques
- **[Adding Custom Preprocessing](adding-custom-preprocessing.md)** — Create your own transformers
- **[Preprocessing Experiments](preprocessing-experiments.md)** — Automated experimentation

### Reference
- **[System Design (SDD)](../SDD.md)** — Architecture and design principles
- **[Configuration Files](../config/)** — Example configurations

## Key Features

- **Clean Architecture**: Modular, testable, and maintainable design
- **Flexible Preprocessing**: Standard and custom preprocessing pipelines
- **Multiple Models**: Train and compare multiple models simultaneously
- **Comprehensive Reporting**: Generate detailed reports in multiple formats
- **Time-Series Support**: Built-in support for EEG and sensor data
- **Cogniflow Integration**: Seamless access via Pygame UI or CLI

## Using Modulus

### Via Cogniflow UI (Easiest)

```bash
poetry run python main.py
# Press [M] for ML Pipeline
```

### Via CLI

```bash
cd modulus
poetry run python run_forward_pipeline.py
```

## Project Context

Modulus was designed as the ML pipeline component for the Cogniflow BCI training system. It handles:

1. **Data Loading** — Reading EEG recordings from `.npy` files
2. **Preprocessing** — Scaling, feature extraction, dimensionality reduction
3. **Model Training** — Multiple classifiers with hyperparameter tuning
4. **Evaluation** — Comprehensive metrics and model comparison
5. **Reporting** — HTML, CSV, and JSON output formats

## See Also

- **[Cogniflow Main README](../../README.md)** — Full project documentation
- **[ModulusScene](../../trainer/scenes/modulus.py)** — Pygame UI integration
- **[Experiment Features](../../docs/modulus/EXPERIMENT_FEATURES.md)** — Advanced experiments

## Contributing

See the main [Cogniflow README](../../README.md) for contribution guidelines.

## License

Part of the Cogniflow research project on EEG-based direction classification.
