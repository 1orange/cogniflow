## Cogniflow — BCI Car Trainer with ML Pipeline

Brain–Computer Interface (BCI) driving trainer built with Pygame, integrated with a modular machine learning pipeline for EEG data analysis and model training.

### Key Features

**BCI Training System:**
- BCI data source via Emotiv EPOC (pyhidapi + AES decrypt)
- Raw data recording wizard with per‑direction selection and parameters
- Pseudo‑3D driving scene with BCI or Arrow‑key control modes
- Modular scene architecture (`Menu`, `Live`, `Record`, `Driving`, `Modulus`, `Settings`)

**ML Pipeline (Modulus):**
- Clean Architecture: Separation of concerns with distinct Domain, Application, Infrastructure layers
- Multiple Data Sources: Support for `.npy` files with embedded metadata
- Reproducible Workflows: Configurable data splitting with seed control
- Flexible Preprocessing: Custom and standard preprocessing pipelines
- Multi-Model Training: Train and compare multiple models simultaneously
- Comprehensive Benchmarking: Automated evaluation with multiple metrics
- Rich Reporting: Export results to CSV, JSON, and HTML formats

## Quick Start

### Requirements
- Python 3.12+
- Linux with HID support (tested on `linux 6.14.x`)
- Emotiv EPOC device (optional - dummy device available for testing)

Python dependencies are defined in `pyproject.toml`.

### Install

See `INSTALL.txt` for detailed installation instructions.

**Quick install (Poetry):**
```bash
# 1. Install Python dependencies
poetry install

# 2. Build and install the Emotiv Rust extension (requires Rust toolchain)
./build_emotiv.sh
```

**System dependencies:**
- **Rust toolchain** (for building emotiv-rs): https://rustup.rs
- **HID libraries** (Linux): `sudo apt install libhidapi-hidraw0 libhidapi-libusb0 libusb-1.0-0`
- **HID libraries** (macOS): `brew install hidapi`

**Note:** The `emotiv-rs` Rust extension is platform-specific and must be built locally. The build script automatically detects your Python version and platform.

### Run
```bash
poetry run python main.py
# or
python main.py
```

## Project Structure

```text
cogniflow/
├─ main.py                 # App entrypoint; runs trainer.main()
├─ config.py               # Global constants (EEG, game, UI)
├─ build_emotiv.sh         # Build and install emotiv-rs extension
├─ INSTALL.txt             # Detailed installation guide
├─ scripts/                # Test and utility scripts
│  ├─ analyzer.py          # Utility to inspect saved .npy data
│  ├─ build_emotiv.py      # Build script for emotiv-rs wheel
│  ├─ check_packets.py     # Monitor Emotiv packet flow
│  └─ test_emotiv_rs.py    # Test suite for emotiv-rs module
├─ data/                   # Saved recordings and metadata
├─ models/                 # Trained model(s), expected model.pkl
├─ trainer/
│  ├─ __init__.py          # Initializes Pygame; launches MenuScene
│  ├─ assets/              # Sprites (car, mountains, road)
│  ├─ scenes/
│  │  ├─ base_scene.py     # Common scene helpers (text, arrows, colors)
│  │  ├─ menu.py           # MenuScene (navigation, model status)
│  │  ├─ calibration.py    # CalibrationScene (trials, async training placeholder)
│  │  ├─ record.py         # RecordScene (wizard + saving)
│  │  ├─ driving.py        # DrivingScene (pseudo‑3D, BCI/Arrow modes)
│  │  ├─ modulus.py        # ModulusScene (ML pipeline interface) ⭐ NEW
│  │  ├─ modulus_model.py  # Model for ModulusScene (MVC)
│  │  ├─ modulus_view.py   # View for ModulusScene (MVC)
│  │  ├─ modulus_controller.py  # Controller for ModulusScene (MVC)
│  │  ├─ settings.py       # SettingsScene (device selection) ⭐ NEW
│  │  ├─ settings_model.py # Model for SettingsScene (MVC)
│  │  ├─ settings_view.py  # View for SettingsScene (MVC)
│  │  └─ settings_controller.py  # Controller for SettingsScene (MVC)
│  └─ utils/
│     ├─ base_scene.py     # (duplicate helper used in utils scope)
│     ├─ car.py            # Car physics and sprite
│     └─ source_manager.py # Device management and data provider initialization ⭐ UPDATED
├─ bci/
│  ├─ utils.py             # LABELS and majority vote helper
│  ├─ data_provider.py     # Threaded buffer over Emotiv EEGReader
│  ├─ devices.py           # Device enumeration and management ⭐ NEW
│  ├─ dummy_provider.py    # Synthetic EEG data generator ⭐ NEW
│  └─ emotiv/              # Low‑level EPOC access (HID, AES, parsing)
│     ├─ reader.py         # High‑level EEGReader API
│     ├─ device.py         # Enumerate/open HID interfaces
│     ├─ sensors.py        # Packet parsing and sensor bit maps
│     ├─ crypto.py         # AES decryption of 32‑byte packets
│     └─ constants.py      # VID/PID, key, sizes
└─ modulus/                # ⭐ ML Pipeline Module (Integrated)
   ├─ modulus/             # Core ML pipeline framework
   │  ├─ domain/           # Domain entities and protocols
   │  ├─ application/      # Use cases and business logic
   │  ├─ infrastructure/   # Data loaders, ML adapters, storage
   │  ├─ config.py         # Configuration handling
   │  └─ container.py      # Dependency injection
   ├─ config/              # Pipeline configuration files
   ├─ data/                # Data directory (shared with cogniflow/data)
   ├─ results/             # ML pipeline results
   ├─ docs/                # ML pipeline documentation
   └─ tests/               # ML pipeline tests
```

## Architecture

### MVC Architecture
All new Python code follows MVC (Model-View-Controller) principles:

- **Model**: Stores state and data structures (e.g., `modulus_model.py`)
- **View**: Handles rendering and display (e.g., `modulus_view.py`)
- **Controller**: Maps input events to model updates (e.g., `modulus_controller.py`)

The ModulusScene demonstrates this architecture with separate Model, View, and Controller classes.

### ML Pipeline Architecture (Modulus)
The Modulus ML pipeline follows Clean Architecture principles:

```
+--------------------------+
|   Presentation Layer     |   <- ModulusScene (Pygame UI)
+--------------------------+
|   Application Core       |   <- Use Cases (Pipeline Execution)
+--------------------------+
|   Domain                 |   <- Entities (Dataset, ModelConfig)
+--------------------------+
|   Infrastructure / I/O  |   <- Data Access, ML Frameworks
+--------------------------+
```

See `modulus/docs/` for detailed ML pipeline documentation.

## Data and Model Flow

### BCI Data Flow
- `bci.emotiv.EEGReader` → `bci.data_provider.DataProvider` (threaded buffer)
- `trainer.utils.SourceManager` constructs the provider and hands it to scenes
- `RecordScene` saves raw windows for offline experiments
- `DrivingScene` consumes commands from either arrow keys or BCI inference

### ML Pipeline Flow
1. Record EEG data using `RecordScene` → saves to `data/`
2. Run ML pipeline using `ModulusScene`:
   - Select configuration from `modulus/config/`
   - Pipeline loads data from `data/`
   - Applies preprocessing
   - Trains models
   - Evaluates and exports results to `modulus/results/`
3. Use trained models in `DrivingScene`

## Configuration

### BCI/Trainer Configuration
All tunables live in `config.py`:
- EEG: `SAMPLE_RATE`, `N_CHANNELS`, `BANDS`, `WIN_SEC`, `HOP_SEC`, artifact gates
- Trainer/game: thresholds, deadzone, speeds, steering factors
- Render: world size, road math, colors

### ML Pipeline Configuration
Configuration files are in `modulus/config/`:
- `example_config.yaml` - Basic example
- `forward_direction_config.yaml` - Forward direction classification
- `eeg_full_preprocessing_config.yaml` - Full EEG preprocessing pipeline
- `advanced_config.yaml` - Advanced configuration options

See `modulus/docs/` for detailed configuration documentation.

## Documentation

### BCI/Trainer Documentation
- `docs/README.md` - Main documentation index
- `docs/EMOTIV_IMPROVEMENTS.md` - Emotiv EPOC improvements
- `docs/emotiv/` - Emotiv technical documentation

### ML Pipeline Documentation
- `modulus/docs/INDEX.md` - Documentation index
- `modulus/docs/quick-start.md` - Quick start guide
- `modulus/docs/preprocessing-modes.md` - Preprocessing modes explained
- `modulus/docs/custom-preprocessing.md` - Custom preprocessing guide
- `modulus/SDD.md` - System Design Document

## Tips & Troubleshooting

### BCI/Trainer
- Emotiv device permissions may require udev rules (run as root once or add a rule if `pyhidapi` cannot open the device).

### ML Pipeline
- Ensure data files are in `data/` directory before running pipeline
- Check configuration file syntax (YAML format)
- Review `modulus/results/` for detailed output
- See `modulus/docs/troubleshooting.md` for common issues

## Development

### Running Tests
```bash
# BCI/Trainer tests
poetry run python scripts/test_emotiv_rs.py

# ML Pipeline tests
cd modulus
pytest
```

### Adding New Scenes
1. Create scene class inheriting from `BaseScene`
2. Follow MVC architecture (separate Model, View, Controller if complex)
3. Add menu option in `MenuScene`
4. Import and instantiate in menu

### Extending ML Pipeline
See `modulus/docs/adding-custom-preprocessing.md` for:
- Adding custom preprocessing transformers
- Extending the framework
- Configuration options

## License

MIT (unless specified otherwise in your distribution).
