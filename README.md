## Cogniflow — BCI Car Trainer

Brain–Computer Interface (BCI) driving trainer built with Pygame. It connects to an Emotiv EPOC headset, streams EEG via HID, and provides a training workflow with calibration, raw data recording, and a pseudo‑3D driving scene.

### Key features
- BCI data source via Emotiv EPOC (pyhidapi + AES decrypt)
- Guided calibration with randomized direction prompts
- Raw data recording wizard with per‑direction selection and parameters
- Pseudo‑3D driving scene with BCI or Arrow‑key control modes
- Modular scene architecture (`Menu`, `Calibration`, `Record`, `Driving`)


## Quick start

### Requirements
- Python 3.11+
- Linux with HID support (tested on `linux 6.14.x`)
- Emotiv EPOC device (Developer headset expected)

Python deps are defined in `pyproject.toml`.

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


## Scenes and what they do

### 1) Menu (`trainer/scenes/menu.py`)
Landing screen to access all flows and show device/model status.
- Shows: title, data source info, sample rate/channels, model status at `models/model.pkl`.
- Navigation keys (in on‑screen order):
  1. `[C] Calibrate`
  2. `[R] Record Data`
  3. `[D] Drive (BCI)`
  4. `[A] Drive (Arrow Keys)`
  5. `[ESC] Quit`

Notes:
- “Drive (BCI)” requires a trained model file (`models/model.pkl`). If not found, a message prompts you to calibrate first.

### 2) Calibration (`trainer/scenes/calibration.py`)
Guided collection of labeled EEG windows for a simple 4‑class control set.
- Labels (from `bci/utils.py` `LABELS`): `left`, `right`, `forward`, `brake`.
- Per trial phases:
  - `baseline` → `task` (show arrow for current label) → `rest`
- Windows are extracted during the `task` phase using sliding windows (`WIN_SEC`, `HOP_SEC`).
- After trials complete, a “Training model…” screen appears; model training is performed asynchronously (placeholder stub present).
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

### 4) Driving (`trainer/scenes/driving.py`)
Pseudo‑3D driving simulator with a fixed virtual resolution scaled to the window.
- Modes: `BCI` or `Arrow` control.
- HUD shows: mode, active commands, last label + confidence (BCI), speed, and a periodic “gate” cue arrow.
- Physics is handled by `trainer/utils/car.py`.

Controls:
- Global: `[ESC]` to return.
- Arrow mode: `[←] left`, `[→] right`, `[↑] forward`, `[↓] backward`.
- BCI mode: hands‑free; commands are inferred from EEG (inference scaffold present; hook your model to enable).


## Order of all buttons/keys

### Menu (on‑screen order)
1. `[C] Calibrate`
2. `[R] Record Data`
3. `[D] Drive (BCI)`
4. `[A] Drive (Arrow Keys)`
5. `[ESC] Quit`

### Record wizard
- Select directions: `[1]..[4]` toggles, `[ENTER]` continue, `[ESC]` cancel
- Window duration: `[UP]/[DOWN]` ±0.5s, `[RIGHT]/[LEFT]` ±0.1s, `[ENTER]` continue, `[ESC]` cancel
- Trials per direction: `[UP]/[DOWN]`, `[ENTER]` continue, `[ESC]` cancel

### Calibration & Recording run
- `[ESC]` to abort/return at any time

### Driving
- `[ESC]` back
- Arrow mode: `[←][→][↑][↓]` as steering/accel/brake


## Project structure
```text
cogniflow/
├─ main.py                 # App entrypoint; runs trainer.main()
├─ config.py               # Global constants (EEG, game, UI)
├─ analyzer.py             # Utility to inspect saved .npy data
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
│  │  └─ driving.py        # DrivingScene (pseudo‑3D, BCI/Arrow modes)
│  └─ utils/
│     ├─ base_scene.py     # (duplicate helper used in utils scope)
│     ├─ car.py            # Car physics and sprite
│     └─ source_manager.py # Initializes EEG data provider
└─ bci/
   ├─ utils.py             # LABELS and majority vote helper
   ├─ data_provider.py     # Threaded buffer over Emotiv EEGReader
   └─ emotiv/              # Low‑level EPOC access (HID, AES, parsing)
      ├─ reader.py         # High‑level EEGReader API
      ├─ device.py         # Enumerate/open HID interfaces
      ├─ sensors.py        # Packet parsing and sensor bit maps
      ├─ crypto.py         # AES decryption of 32‑byte packets
      └─ constants.py      # VID/PID, key, sizes
```


## Data and model flow (high level)
- `bci.emotiv.EEGReader` → `bci.data_provider.DataProvider` (threaded buffer)
- `trainer.utils.SourceManager` constructs the provider and hands it to scenes
- `CalibrationScene` collects labeled windows and triggers model training (stub)
- `RecordScene` saves raw windows for offline experiments
- `DrivingScene` consumes commands from either arrow keys or BCI inference


## Configuration
All tunables live in `config.py`:
- EEG: `SAMPLE_RATE`, `N_CHANNELS`, `BANDS`, `WIN_SEC`, `HOP_SEC`, artifact gates
- Trainer/game: thresholds, deadzone, speeds, steering factors
- Render: world size, road math, colors


## Tips & troubleshooting
- Emotiv device permissions may require udev rules (run as root once or add a rule if `pyhidapi` cannot open the device).
- If `models/model.pkl` is missing, “Drive (BCI)” will show a warning; run Calibration first to create/train a model (training hook is currently a placeholder – integrate your pipeline).
- Use `analyzer.py` to quickly open an `.npy` file and print its basic info:
  ```bash
  python analyzer.py
  ```


## License
MIT (unless specified otherwise in your distribution).