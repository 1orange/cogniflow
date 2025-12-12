# BCI Car Trainer - Documentation

The BCI Car Trainer is an interactive application for training and testing brain-computer interface (BCI) control using EEG signals from the Emotiv EPOC headset.

## 📖 Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Architecture](#architecture)
4. [Scenes](#scenes)
5. [Configuration](#configuration)
6. [BCI Control](#bci-control)
7. [Data Recording](#data-recording)
8. [Troubleshooting](#troubleshooting)

## Overview

The BCI Car Trainer is a pygame-based application that allows users to:

- **Calibrate** their BCI model by recording labeled EEG data
- **Record** raw EEG data for later analysis
- **Drive** a pseudo-3D car using either:
  - **BCI mode**: Control with brain signals
  - **Arrow key mode**: Control with keyboard (for testing/comparison)

### Key Features

- ✅ Real-time EEG signal processing
- ✅ Multiple control modes (BCI and keyboard)
- ✅ Pseudo-3D racing game environment
- ✅ Calibration and data recording system
- ✅ Model training with balanced accuracy metrics
- ✅ Asynchronous signal processing for smooth gameplay

## Getting Started

### Installation

```bash
# Clone the repository (if not already done)
cd /home/jean/dev/diplomka/cogniflow

# Install dependencies
poetry install

# Build Emotiv Rust extension (if not already done)
cd bci/emotiv/lib
bash install_dev.sh
```

### Running the Trainer

```bash
# From the project root
poetry run python main.py

# Or directly
python main.py
```

### Quick Start Workflow

1. **Launch the application**
   ```bash
   poetry run python main.py
   ```

2. **Select a device** ⭐ **NEW**
   - Press `S` to open device settings
   - Choose between Emotiv EPOC (if connected) or Dummy Device
   - Press `ENTER` to connect
   - Press `ESC` to return to menu

3. **Connect your Emotiv EPOC headset** (if using real device)
   - Ensure all sensors have good contact (quality > 3)
   - Check battery level (> 20%)
   - Press `R` in Settings to refresh if not detected

4. **Calibrate (First time)**
   - Press `C` to enter calibration mode
   - Follow on-screen arrows for each direction
   - Wait for model training to complete

5. **Drive with BCI**
   - Press `D` to enter BCI driving mode
   - Think about the calibrated directions to control the car

6. **Practice with Arrow Keys**
   - Press `A` to practice with keyboard controls
   - Get familiar with the game physics

## Architecture

### Project Structure

```
trainer/
├── __init__.py              # Main entry point
├── scenes/                  # Game scenes
│   ├── base_scene.py        # Base class for all scenes
│   ├── menu.py              # Main menu
│   ├── settings.py          # Device selection ⭐ NEW
│   ├── calibration.py       # BCI calibration
│   ├── record.py            # Data recording
│   └── driving.py           # Driving game
├── utils/                   # Utility classes
│   ├── car.py               # Car physics and rendering
│   └── source_manager.py    # Device management and EEG source ⭐ UPDATED
└── assets/                  # Game assets
    ├── car.png              # Car sprite
    ├── road.png             # Road texture
    ├── mountains.png        # Background
    └── ...
```

### Components

#### 1. Scenes

Each scene is a self-contained game state:

- **MenuScene**: Main navigation hub
- **SettingsScene**: Device selection and configuration ⭐ **NEW**
- **CalibrationScene**: BCI model training
- **RecordScene**: Raw data collection
- **DrivingScene**: Main gameplay

#### 2. Device Management

The application uses a centralized `SourceManager` to handle device selection:

```
Device Enumeration (bci/devices.py)
     ↓
SourceManager (trainer/utils/source_manager.py)
     ↓
Device Selection (Settings Scene)
     ↓
Data Provider Initialization
     ├─ Emotiv EPOC → DataProvider
     └─ Dummy Device → DummyDataProvider
```

**Key Components:**
- `bci/devices.py`: Device enumeration and information structures
- `bci/dummy_provider.py`: Synthetic EEG data generator
- `trainer/utils/source_manager.py`: Centralized device management (singleton)
- `trainer/scenes/settings.py`: Device selection UI (MVC architecture)

#### 3. EEG Processing Pipeline

```
Selected Device (Emotiv or Dummy)
     ↓
USB HID Reader (Rust) / Synthetic Generator
     ↓
AES Decryption (Rust) / Direct Signal Generation
     ↓
Python EEG Reader / Dummy Provider
     ↓
Signal Buffering
     ↓
Feature Extraction
     ↓
ML Model Prediction
     ↓
Majority Voting
     ↓
Car Control Commands
```

#### 4. Car Physics

Pseudo-3D racing physics with:
- Acceleration/deceleration
- Steering with velocity-dependent turning
- Road following with curves and inclines
- Collision detection

## Scenes

### 1. Menu Scene

**Purpose:** Main navigation and system status

**Controls:**
- `S` - Open device settings ⭐ **NEW**
- `C` - Enter calibration mode
- `R` - Enter data recording mode
- `D` - Drive with BCI (requires calibrated model)
- `A` - Drive with arrow keys
- `ESC` - Quit application

**Display Information:**
- Current device name (Emotiv EPOC or Dummy Device)
- Sample rate and channel count
- Model availability status

### 2. Settings Scene ⭐ **NEW**

**Purpose:** Select and configure EEG data sources

**Features:**
- View all available devices (Emotiv EPOC, Dummy Device)
- Select which device to use for recording and BCI
- Refresh device list to detect newly connected devices
- Visual device browser with connection status

**Supported Devices:**
- 🧠 **Emotiv EPOC** - Real EEG headset (14 channels, 128 Hz)
  - Automatic detection via HID enumeration
  - Shows device serial numbers and VID/PID
- 🔧 **Dummy Device** - Simulated data for testing/development
  - Generates synthetic EEG-like signals
  - Includes alpha, beta, and theta waves
  - Useful for testing without hardware

**Controls:**
- `↑/↓` - Navigate device list
- `ENTER` - Connect to selected device
- `R` - Refresh device list
- `ESC` - Return to menu

**Usage:**
1. Press `S` from main menu
2. Use arrow keys to select a device
3. Press `ENTER` to connect
4. Press `R` to refresh if device not detected
5. Press `ESC` to return

**Dummy Device:**
The dummy device generates synthetic EEG-like signals including:
- Alpha waves (8-12 Hz) - dominant when relaxed
- Beta waves (12-30 Hz) - active thinking
- Theta waves (4-8 Hz) - drowsy/meditative states
- Random noise and occasional artifacts

This is useful for testing the application without requiring real EEG hardware.

### 3. Calibration Scene

**Purpose:** Train the BCI model by recording labeled EEG data

**Process:**

1. **Baseline Phase** (1.5s)
   - Relax and look at blank screen
   - Establishes baseline brain activity

2. **Task Phase** (4.0s)
   - Arrow appears showing direction
   - Think about/imagine the direction
   - EEG windows are labeled and recorded

3. **Rest Phase** (2.0s)
   - Blank screen between trials
   - Prevents fatigue

**Controls:**
- `ESC` - Abort calibration

**Configuration:**
- `TRIALS_PER_CLASS = 8` - Trials per direction
- `BASELINE_SEC = 1.5` - Baseline duration
- `TASK_SEC = 4.0` - Task duration
- `REST_SEC = 2.0` - Rest duration

**Output:**
- Trained model saved to `models/model.pkl`
- Balanced accuracy metric displayed

**Labels:**
- `left` - Think about turning left
- `right` - Think about turning right
- `forward` - Think about moving forward
- `brake` - Think about stopping

### 4. Record Scene

**Purpose:** Record raw EEG data for analysis

**Features:**

#### Direction Selection
- Choose which directions to record
- Press `1-4` to toggle directions
- Press `ENTER` to continue

#### Window Duration
- Adjust recording window length
- `UP/DOWN` - Coarse adjustment (0.5s steps)
- `LEFT/RIGHT` - Fine adjustment (0.1s steps)
- Default: 4.0 seconds

#### Trial Count
- Set number of trials per direction
- `UP/DOWN` - Adjust count
- Default: 8 trials per direction

**Controls:**
- `ESC` - Cancel recording

**Output:**
- Raw data saved to `data/recorded_data_{direction}_{timestamp}.npy`
- Metadata saved to `data/metadata_{direction}_{timestamp}.txt`

**Data Format:**
- NumPy array: `(n_windows, window_length, n_channels)`
- Window length: `WIN_SEC * SAMPLE_RATE` samples
- Channels: 14 EEG sensors from EPOC

### 5. Driving Scene

**Purpose:** Main gameplay - drive the car in a pseudo-3D environment

**Control Modes:**

#### BCI Mode (`control_mode="bci"`)
- Real-time EEG signal processing
- Majority voting for command stability
- Deadzone to prevent command spam
- Visual feedback showing active commands

#### Arrow Key Mode (`control_mode="arrow"`)
- Direct keyboard control
- Multiple simultaneous commands
- Useful for testing and comparison

**Controls (Arrow Mode):**
- `UP` - Accelerate forward
- `DOWN` - Brake/reverse
- `LEFT` - Steer left
- `RIGHT` - Steer right
- `ESC` - Return to menu

**Display Information:**
- Current mode (BCI or ARROW)
- Active commands
- Last BCI prediction (BCI mode only)
- Prediction confidence (BCI mode only)
- Current speed

**Game Physics:**

```python
# Acceleration
PLAYER_ACCELERATION_FORCE = 4
PLAYER_BRAKE_FORCE = 1
PLAYER_DRAG_FACTOR = 0.5

# Velocity limits
PLAYER_MAX_VELOCITY = 20
PLAYER_MIN_VELOCITY = -10

# Steering
PLAYER_STEERING_FACTOR = 10
PLAYER_MAX_ANGLE = 0.8
PLAYER_MIN_ANGLE = -0.8
```

**Road Generation:**
- Procedural curves using sine functions
- Dynamic inclines for height variation
- Collision detection off-road

**Rendering:**
- Low-res virtual world (320×180)
- Scaled to window size with letterboxing
- Maintains crisp UI text
- Pseudo-3D perspective projection

**BCI Gate System:**
- Periodic target directions appear
- Used to measure BCI accuracy during gameplay
- Can be ignored in free-drive mode

## Configuration

All configuration is centralized in `config.py`:

### EEG Settings

```python
DATA_SOURCE = "emotiv"      # Data source
SAMPLE_RATE = 128           # Hz (Emotiv EPOC rate)
N_CHANNELS = 14             # 14 EEG sensors

# Preprocessing
BANDPASS = (1.0, 40.0)      # Hz - bandpass filter range
NOTCH = 50.0                # Hz - notch filter (power line)
ARTIFACT_UV = 120.0         # Artifact rejection threshold
```

### Windowing

```python
WIN_SEC = 1.5               # Window size in seconds
HOP_SEC = 0.5               # Hop size (overlap)
BANDS = [                   # Frequency bands for features
    (4, 8),                 # Theta
    (8, 12),                # Alpha
    (12, 16),               # Low beta
    (16, 22),               # Mid beta
    (22, 30)                # High beta
]
```

### BCI Control

```python
CONF_THRESHOLD = 0.60       # Minimum confidence for command
MAJORITY_K = 5              # History size for majority vote
NOOP_LABEL = "noop"         # No operation label
```

### Calibration

```python
TRIALS_PER_CLASS = 8        # Trials per direction
BASELINE_SEC = 1.5          # Baseline phase duration
TASK_SEC = 4.0              # Task phase duration
REST_SEC = 2.0              # Rest phase duration
```

### Game Physics

```python
# Driving behavior
TURN_HOLD_FRAMES = 2        # Frames to hold turn command
DEADZONE_SEC = 0.6          # Cooldown between commands
MAX_SPEED = 180.0           # Maximum car speed
TURN_RATE = 140.0           # Turning rate

# Display
SCREEN_WIDTH = 320          # Virtual screen width
SCREEN_HEIGHT = 180         # Virtual screen height

# Player physics (see previous section)
```

### Road Generation

```python
# Curve generation
ROAD_CURVE_FREQUENCY_1 = 17
ROAD_CURVE_AMPLITUDE_1 = 200
ROAD_CURVE_FREQUENCY_2 = 8
ROAD_CURVE_AMPLITUDE_2 = 170

# Incline generation
ROAD_INCLINE_FREQUENCY_1 = 13
ROAD_INCLINE_AMPLITUDE_1 = 80
ROAD_INCLINE_FREQUENCY_2 = 7
ROAD_INCLINE_AMPLITUDE_2 = 120
ROAD_INCLINE_BASE = 200

# Collision
COLLISION_THRESHOLD = 280
COLLISION_MIN_VELOCITY = 5
```

## BCI Control

### Signal Processing Pipeline

#### 1. Data Acquisition

```python
# Read samples from Emotiv headset
samples = source.read(n_samples)
# Shape: (n_samples, 14 channels)
```

#### 2. Buffering

```python
# Maintain sliding window buffer
chan_buf = np.vstack([chan_buf, samples])
# Keep last 2-3 windows for processing
```

#### 3. Windowing

```python
# Extract windows with overlap
win_len = int(WIN_SEC * SAMPLE_RATE)  # e.g., 192 samples
hop = int(HOP_SEC * SAMPLE_RATE)      # e.g., 64 samples

while chan_buf.shape[0] >= win_len:
    win = chan_buf[:win_len, :]
    chan_buf = chan_buf[hop:, :]
    # Process window...
```

#### 4. Feature Extraction

Features extracted from each window:
- **Band power**: Power in each frequency band (5 bands)
- **Channels**: All 14 EEG sensors
- **Total features**: ~70 features per window

#### 5. Classification

```python
# Predict with trained model
proba = model.predict_proba(features)
# Returns probability for each label

# Filter by confidence threshold
active_commands = [
    label for label, conf in proba.items()
    if conf >= CONF_THRESHOLD
]
```

#### 6. Majority Voting

```python
# Stabilize predictions with history
hist.append((label, confidence))
label, conf = majority_vote(hist, k=MAJORITY_K)
```

#### 7. Command Execution

```python
# Apply deadzone to prevent spam
if time.time() >= dead_until:
    car.update(dt, [label])
    dead_until = time.time() + DEADZONE_SEC
```

### Asynchronous Processing

To maintain smooth 60 FPS gameplay:

```python
# BCI processing runs in separate thread
executor = ThreadPoolExecutor(max_workers=2)

# Submit window for processing
future = executor.submit(process_bci_async, window)

# Check result without blocking
if future.done():
    commands = future.result()
    car.update(dt, commands)
```

### Optimizing BCI Performance

#### 1. Signal Quality
- Ensure all sensors have quality ≥ 3 (Fair or better)
- Moisten sensor pads if needed
- Check for good scalp contact

#### 2. Calibration Tips
- Sit comfortably and relaxed
- Focus on distinct mental tasks:
  - **Left**: Imagine moving your left hand
  - **Right**: Imagine moving your right hand
  - **Forward**: Imagine pushing forward
  - **Brake**: Imagine stopping/tensing
- Be consistent across all trials
- Avoid head movement during calibration

#### 3. Configuration Tuning
```python
# More stable but slower response
CONF_THRESHOLD = 0.70
MAJORITY_K = 7
DEADZONE_SEC = 0.8

# Faster but less stable response
CONF_THRESHOLD = 0.50
MAJORITY_K = 3
DEADZONE_SEC = 0.4
```

## Data Recording

### Purpose

Record raw EEG data for:
- Offline analysis
- Model improvement
- Research purposes
- Custom feature extraction

### Output Files

For each direction recorded:

#### Data File (`recorded_data_{direction}_{timestamp}.npy`)
```python
# Load recorded data
data = np.load('data/recorded_data_left_20251102_143052.npy')

# Shape: (n_windows, window_length, n_channels)
# Example: (45, 192, 14)
#   45 windows
#   192 samples per window (1.5s * 128 Hz)
#   14 EEG channels
```

#### Metadata File (`metadata_{direction}_{timestamp}.txt`)
```
Direction: left
Timestamp: 20251102_143052
Sample rate: 128 Hz
Channels: 14
Window length: 1.5 seconds
Hop length: 0.5 seconds
Number of windows: 45
Data shape: (45, 192, 14)
```

### Using Recorded Data

```python
import numpy as np

# Load data
data = np.load('data/recorded_data_left_20251102_143052.npy')

# Access individual windows
window_0 = data[0]  # Shape: (192, 14)

# Access specific channel
channel_F3 = window_0[:, 0]  # F3 channel data

# Compute statistics
mean_power = np.mean(np.abs(data), axis=(1, 2))
print(f"Average power per window: {mean_power}")
```

## Troubleshooting

### Headset Connection Issues

**Problem:** "No matching Emotiv device found"

**Solutions:**
1. Check USB connection
2. Try different USB port
3. Verify headset is powered on
4. Check battery level
5. Run lsusb to verify device is detected:
   ```bash
   lsusb | grep -i emotiv
   ```

### Poor Signal Quality

**Problem:** All sensors show quality 0 or 1

**Solutions:**
1. Moisten sensor pads with saline solution
2. Ensure good scalp contact
3. Move hair away from sensors
4. Wait 2-3 minutes for sensors to settle
5. Check headset positioning

### BCI Not Responding

**Problem:** Car doesn't respond to brain signals

**Solutions:**
1. Check model exists: `ls models/model.pkl`
2. Recalibrate if model is old
3. Verify signal quality (all sensors > 3)
4. Check confidence threshold in config.py
5. Try arrow key mode first to verify game works

### Low FPS / Laggy Performance

**Problem:** Game runs slowly

**Solutions:**
1. Close other applications
2. Reduce window size (press F11 for fullscreen toggle)
3. Check CPU usage
4. Ensure Rust extension is built in release mode:
   ```bash
   cd bci/emotiv/lib
   maturin develop --release
   ```

### Calibration Accuracy Too Low

**Problem:** "Hold-out balanced acc: 0.35" (< 0.5)

**Solutions:**
1. Ensure better signal quality during calibration
2. Be more consistent with mental tasks
3. Increase `TRIALS_PER_CLASS` to 12-15
4. Focus more intensely on each direction
5. Avoid distractions during calibration
6. Ensure you're well-rested

### Model Not Saving

**Problem:** Model file not created after calibration

**Solutions:**
1. Check `models/` directory exists:
   ```bash
   mkdir -p models
   ```
2. Verify write permissions
3. Check console for error messages
4. Ensure calibration completed (not interrupted with ESC)

## Advanced Topics

### Custom Feature Extraction

Modify feature extraction in the BCI pipeline:

```python
def extract_features(window):
    """
    Custom feature extraction from EEG window.
    
    Args:
        window: (samples, channels) EEG data
        
    Returns:
        Feature vector
    """
    features = []
    
    # Your custom features here
    # e.g., wavelets, entropy, complexity metrics
    
    return np.array(features)
```

### Model Selection

The default implementation uses a placeholder for the ML model. Common choices:

- **Random Forest**: Good balance, interpretable
- **SVM**: High accuracy, slower
- **LDA**: Fast, simple, works well for EEG
- **Neural Networks**: Best accuracy, requires more data

### Real-time Performance Monitoring

Add performance metrics to the driving scene:

```python
# Track BCI accuracy against gates
if self.gate_label and predicted_label == self.gate_label:
    accuracy_counter += 1
total_gates += 1
accuracy = accuracy_counter / total_gates
```

## See Also

- [Emotiv EPOC Documentation](../emotiv/README_IMPROVEMENTS.md)
- [Packet Structure Reference](../emotiv/PACKET_STRUCTURE.md)
- [Configuration Reference](CONFIGURATION.md)
- [BCI Pipeline Details](BCI_PIPELINE.md)

