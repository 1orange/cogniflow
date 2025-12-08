## Cogniflow — BCI Car Trainer with ML Pipeline

Brain–Computer Interface (BCI) driving trainer built with Pygame, integrated with a modular machine learning pipeline for EEG data analysis and model training.

### Key Features

**BCI Training System:**
- BCI data source via Emotiv EPOC (pyhidapi + AES decrypt)
- Guided calibration with randomized direction prompts
- Raw data recording wizard with per‑direction selection and parameters
- Pseudo‑3D driving scene with BCI or Arrow‑key control modes
- Modular scene architecture (`Menu`, `Calibration`, `Record`, `Driving`, `Modulus`)

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
- Python 3.11+
- Linux with HID support (tested on `linux 6.14.x`)
- Emotiv EPOC device (Developer headset expected)

Python dependencies are defined in `pyproject.toml`.

### Install

Using Poetry (recommended):
```bash
poetry install
```

Using pip (alternative):
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r <(python - <<'PY'
import tomllib, sys
data=tomllib.loads(open('pyproject.toml','rb').read())
print('\n'.join(data['project']['dependencies']))
PY
)
```

You may need system packages for HID (examples):
- `sudo apt install libhidapi-hidraw0 libhidapi-libusb0 libusb-1.0-0`

### Run
```bash
poetry run python main.py
# or
python main.py
```

## Scenes and What They Do

### 1) Menu (`trainer/scenes/menu.py`)
Landing screen to access all flows and show device/model status.
- Shows: title, data source info, sample rate/channels, model status at `models/model.pkl`.
- Navigation keys (in on‑screen order):
  1. `[C] Calibrate`
  2. `[R] Record Data`
  3. `[M] ML Pipeline (Modulus)` ⭐ **NEW**
  4. `[D] Drive (BCI)`
  5. `[A] Drive (Arrow Keys)`
  6. `[ESC] Quit`

Notes:
- "Drive (BCI)" requires a trained model file (`models/model.pkl`). If not found, a message prompts you to calibrate first.
- "ML Pipeline (Modulus)" launches the integrated ML pipeline interface for training models on recorded EEG data.

### 2) Calibration (`trainer/scenes/calibration.py`)
Guided collection of labeled EEG windows for a simple 4‑class control set.
- Labels (from `bci/utils.py` `LABELS`): `left`, `right`, `forward`, `brake`.
- Per trial phases:
  - `baseline` → `task` (show arrow for current label) → `rest`
- Windows are extracted during the `task` phase using sliding windows (`WIN_SEC`, `HOP_SEC`).
- After trials complete, a "Training model…" screen appears; model training is performed asynchronously (placeholder stub present).
- Completion screen shows a balanced accuracy readout and instructs `[ESC]` to return.

Controls:
- `[ESC]` aborts and returns to previous screen.

### 3) Record (`trainer/scenes/record.py`)
Wizard to record raw EEG windows per direction for offline analysis.
Flow:
1. Select directions to record (default all on). Toggle with `[1]…[4]` in the order of `LABELS`. Confirm `[ENTER]`, cancel `[ESC]`.
2. Set window duration: adjust with `[UP]/[DOWN]` (±0.5s), fine tune `[RIGHT]/[LEFT]` (±0.1s). Confirm `[ENTER]`, cancel `[ESC]`.
3. Set number of trials per selected direction: `[UP]/[DOWN]`. Confirm `[ENTER]`, cancel `[ESC]`.
4. Recording runs by randomized order, with the same `baseline → task → rest` phases and arrow prompts during `task`.

Outputs (per selected direction):
- `data/recorded_data_<direction>_<timestamp>.npy` — stacked windows (NumPy array)
- `data/metadata_<direction>_<timestamp>.txt` — parameters and shapes

Controls:
- Throughout the wizard and recording: `[ESC]` to cancel/return.

### 4) ML Pipeline / Modulus (`trainer/scenes/modulus.py`) ⭐ **NEW**
Integrated interface for running the Modulus ML pipeline on recorded EEG data.

**Features:**
- Configuration file selection from `modulus/config/` directory
- Visual pipeline execution with progress updates
- Results display and error handling
- Follows MVC architecture (Model-View-Controller)

**Usage:**
1. Select a configuration file using `[UP]/[DOWN]` arrows
2. Press `[ENTER]` to run the pipeline
3. View progress and results
4. Press `[ESC]` to return to menu

**Configuration Files:**
- Located in `modulus/config/` directory
- Examples: `example_config.yaml`, `forward_direction_config.yaml`, `eeg_full_preprocessing_config.yaml`
- See `modulus/docs/` for detailed configuration guide

**Pipeline Steps:**
1. Load data from `data/` directory
2. Split into train/validation/test sets
3. Apply preprocessing pipeline
4. Train multiple models
5. Evaluate on validation and test sets
6. Export results to `modulus/results/`

Controls:
- `[UP]/[DOWN]` - Navigate configuration files
- `[ENTER]` - Run selected pipeline
- `[ESC]` - Return to menu

### 5) Driving (`trainer/scenes/driving.py`)
Pseudo‑3D driving simulator with a fixed virtual resolution scaled to the window.
- Modes: `BCI` or `Arrow` control.
- HUD shows: mode, active commands, last label + confidence (BCI), speed, and a periodic "gate" cue arrow.
- Physics is handled by `trainer/utils/car.py`.

Controls:
- Global: `[ESC]` to return.
- Arrow mode: `[←] left`, `[→] right`, `[↑] forward`, `[↓] backward`.
- BCI mode: hands‑free; commands are inferred from EEG (inference scaffold present; hook your model to enable).

## Order of All Buttons/Keys

### Menu (on‑screen order)
1. `[C] Calibrate`
2. `[R] Record Data`
3. `[M] ML Pipeline (Modulus)` ⭐
4. `[D] Drive (BCI)`
5. `[A] Drive (Arrow Keys)`
6. `[ESC] Quit`

### Record wizard
- Select directions: `[1]..[4]` toggles, `[ENTER]` continue, `[ESC]` cancel
- Window duration: `[UP]/[DOWN]` ±0.5s, `[RIGHT]/[LEFT]` ±0.1s, `[ENTER]` continue, `[ESC]` cancel
- Trials per direction: `[UP]/[DOWN]`, `[ENTER]` continue, `[ESC]` cancel

### Modulus ML Pipeline
- `[UP]/[DOWN]` - Select configuration file
- `[ENTER]` - Run pipeline
- `[ESC]` - Return to menu

### Calibration & Recording run
- `[ESC]` to abort/return at any time

### Driving
- `[ESC]` back
- Arrow mode: `[←][→][↑][↓]` as steering/accel/brake

## Project Structure

```text
cogniflow/
├─ main.py                 # App entrypoint; runs trainer.main()
├─ config.py               # Global constants (EEG, game, UI)
├─ scripts/                # Test and utility scripts
│  ├─ analyzer.py          # Utility to inspect saved .npy data
│  ├─ check_packets.py      # Monitor Emotiv packet flow
│  └─ test_emotiv_rs.py     # Test suite for emotiv-rs module
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
│  │  └─ modulus_controller.py  # Controller for ModulusScene (MVC)
│  └─ utils/
│     ├─ base_scene.py     # (duplicate helper used in utils scope)
│     ├─ car.py            # Car physics and sprite
│     └─ source_manager.py # Initializes EEG data provider
├─ bci/
│  ├─ utils.py             # LABELS and majority vote helper
│  ├─ data_provider.py     # Threaded buffer over Emotiv EEGReader
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
- `CalibrationScene` collects labeled windows and triggers model training (stub)
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
3. Use trained models in `CalibrationScene` or `DrivingScene`

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
- If `models/model.pkl` is missing, "Drive (BCI)" will show a warning; run Calibration first to create/train a model (training hook is currently a placeholder – integrate your pipeline).
- Use `scripts/analyzer.py` to quickly open an `.npy` file and print its basic info:
  ```bash
  python scripts/analyzer.py
  ```

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
