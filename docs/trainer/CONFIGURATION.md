# Configuration Reference

Complete reference for all configuration parameters in `config.py`.

## Table of Contents

- [Data Source](#data-source)
- [EEG Parameters](#eeg-parameters)
- [Signal Processing](#signal-processing)
- [BCI Control](#bci-control)
- [Calibration](#calibration)
- [Game Physics](#game-physics)
- [Visual Settings](#visual-settings)
- [Road Generation](#road-generation)

## Data Source

### Device Selection

Device selection is now handled through the Settings scene (`[S]` from main menu) rather than configuration files. The application supports:

- **Emotiv EPOC**: Real EEG headset (14 channels, 128 Hz)
- **Dummy Device**: Synthetic data generator for testing

Device selection is managed by `SourceManager` (singleton pattern) and persists across scenes.

### Legacy `DATA_SOURCE` (Deprecated)

**Note:** The `DATA_SOURCE` configuration parameter is deprecated. Use the Settings scene to select devices instead.

- **Type:** `str`
- **Default:** `"emotiv"`
- **Description:** Legacy EEG data source identifier
- **Options:** `"emotiv"` (deprecated - use Settings scene)

## EEG Parameters

### `SAMPLE_RATE`
- **Type:** `int`
- **Default:** `128`
- **Units:** Hz
- **Description:** EEG sampling frequency
- **Notes:** Emotiv EPOC samples at 128 Hz (fixed)

### `N_CHANNELS`
- **Type:** `int`
- **Default:** `14`
- **Description:** Number of EEG channels
- **Notes:** Emotiv EPOC has 14 sensors (F3, FC5, AF3, F7, T7, P7, O1, O2, P8, T8, FC6, F4, F8, AF4)

## Signal Processing

### `BANDPASS`
- **Type:** `tuple[float, float]`
- **Default:** `(1.0, 40.0)`
- **Units:** Hz
- **Description:** Bandpass filter frequency range (low_cut, high_cut)
- **Recommended ranges:**
  - `(1.0, 40.0)` - General EEG (default)
  - `(0.5, 50.0)` - Wider range
  - `(4.0, 30.0)` - Focus on motor imagery bands

### `NOTCH`
- **Type:** `float`
- **Default:** `50.0`
- **Units:** Hz
- **Description:** Notch filter frequency to remove power line interference
- **Options:**
  - `50.0` - Europe, Asia, Africa, Australia
  - `60.0` - North America, parts of Asia
  - `None` - Disable notch filter

### `ARTIFACT_UV`
- **Type:** `float`
- **Default:** `120.0`
- **Units:** μV (microvolts)
- **Description:** Artifact rejection threshold
- **Behavior:** Windows with samples exceeding this absolute amplitude are rejected
- **Tuning:**
  - **Higher (e.g., 150)**: Keep more data, but may include artifacts
  - **Lower (e.g., 80)**: Stricter rejection, cleaner data but may lose valid data

### `WIN_SEC`
- **Type:** `float`
- **Default:** `1.5`
- **Units:** seconds
- **Description:** Window size for feature extraction
- **Formula:** `window_length = WIN_SEC * SAMPLE_RATE` samples
- **Trade-offs:**
  - **Longer (e.g., 2.0s)**: More stable features, slower response
  - **Shorter (e.g., 1.0s)**: Faster response, less stable features

### `HOP_SEC`
- **Type:** `float`
- **Default:** `0.5`
- **Units:** seconds
- **Description:** Hop size between windows (overlap)
- **Formula:** `hop_length = HOP_SEC * SAMPLE_RATE` samples
- **Overlap:** `overlap = WIN_SEC - HOP_SEC` seconds
- **Trade-offs:**
  - **Smaller hop (e.g., 0.25s)**: More frequent updates, higher CPU usage
  - **Larger hop (e.g., 1.0s)**: Less frequent updates, lower CPU usage

### `BANDS`
- **Type:** `list[tuple[float, float]]`
- **Default:** `[(4, 8), (8, 12), (12, 16), (16, 22), (22, 30)]`
- **Units:** Hz
- **Description:** Frequency bands for power spectral density features
- **Default bands:**
  - `(4, 8)` - **Theta**: Drowsiness, meditation
  - `(8, 12)` - **Alpha**: Relaxation, eyes closed
  - `(12, 16)` - **Low Beta**: Attention, active thinking
  - `(16, 22)` - **Mid Beta**: Focus, motor activity
  - `(22, 30)` - **High Beta**: Alertness, anxiety

**Alternative configurations:**
```python
# Classic EEG bands
BANDS = [
    (4, 8),    # Theta
    (8, 13),   # Alpha
    (13, 30),  # Beta
    (30, 50)   # Gamma
]

# Motor imagery focused
BANDS = [
    (8, 13),   # Mu rhythm
    (13, 30),  # Beta
    (30, 40)   # Low gamma
]
```

## BCI Control

### `CONF_THRESHOLD`
- **Type:** `float`
- **Default:** `0.60`
- **Range:** `0.0 - 1.0`
- **Description:** Minimum prediction confidence to execute command
- **Behavior:** Predictions below this threshold are ignored
- **Tuning:**
  - **Higher (e.g., 0.75)**: More selective, fewer false positives, slower response
  - **Lower (e.g., 0.45)**: More responsive, more false positives

### `MAJORITY_K`
- **Type:** `int`
- **Default:** `5`
- **Description:** Number of recent predictions used for majority voting
- **Behavior:** Command is executed only if it appears most frequently in last K predictions
- **Tuning:**
  - **Higher (e.g., 7-10)**: More stable, slower to change direction
  - **Lower (e.g., 3)**: More responsive, less stable

### `NOOP_LABEL`
- **Type:** `str`
- **Default:** `"noop"`
- **Description:** Label for "no operation" class (if used)
- **Notes:** Currently not actively used; reserved for future use

## Calibration

### `TRIALS_PER_CLASS`
- **Type:** `int`
- **Default:** `8`
- **Description:** Number of trials to record for each direction during calibration
- **Total trials:** `TRIALS_PER_CLASS * number_of_labels` (e.g., 8 * 4 = 32 trials)
- **Recommendations:**
  - **Minimum**: 5-6 trials per class (quick calibration)
  - **Recommended**: 8-10 trials per class (balanced)
  - **High accuracy**: 12-15 trials per class (longer calibration)

### `BASELINE_SEC`
- **Type:** `float`
- **Default:** `1.5`
- **Units:** seconds
- **Description:** Duration of baseline (rest) phase before each task
- **Purpose:** Establish neutral brain activity level
- **Recommendations:**
  - **Minimum**: 1.0 second
  - **Standard**: 1.5-2.0 seconds
  - **Relaxation needed**: 2.5-3.0 seconds

### `TASK_SEC`
- **Type:** `float`
- **Default:** `4.0`
- **Units:** seconds
- **Description:** Duration of task (imagined movement) phase
- **Purpose:** Time to perform the mental task while EEG is recorded
- **Recommendations:**
  - **Quick training**: 3.0 seconds
  - **Standard**: 4.0-5.0 seconds
  - **Deep focus**: 6.0-8.0 seconds

### `REST_SEC`
- **Type:** `float`
- **Default:** `2.0`
- **Units:** seconds
- **Description:** Duration of rest phase between trials
- **Purpose:** Prevent mental fatigue and allow brain state to reset
- **Recommendations:**
  - **Fast pace**: 1.5 seconds
  - **Standard**: 2.0-2.5 seconds
  - **Prevent fatigue**: 3.0-4.0 seconds

## Game Physics

### Car Control

#### `TURN_HOLD_FRAMES`
- **Type:** `int`
- **Default:** `2`
- **Description:** Number of consecutive frames a command must be predicted to be executed
- **Purpose:** Reduces noise and accidental commands
- **Tuning:**
  - **1**: Immediate response, more noise
  - **2-3**: Balanced (recommended)
  - **4-5**: Very stable, slower to respond

#### `DEADZONE_SEC`
- **Type:** `float`
- **Default:** `0.6`
- **Units:** seconds
- **Description:** Cooldown period after executing a BCI command
- **Purpose:** Prevents command spam and allows time for intention to change
- **Tuning:**
  - **0.3-0.4**: Fast response, may feel twitchy
  - **0.5-0.7**: Balanced control (recommended)
  - **0.8-1.0**: Deliberate control, slower

#### `MAX_SPEED`
- **Type:** `float`
- **Default:** `180.0`
- **Description:** Maximum display speed value
- **Notes:** Visual only, doesn't affect actual physics

#### `TURN_RATE`
- **Type:** `float`
- **Default:** `140.0`
- **Description:** Turning rate multiplier
- **Notes:** Visual only, doesn't affect actual physics

### Player Physics

#### `PLAYER_MAX_VELOCITY`
- **Type:** `float`
- **Default:** `20`
- **Description:** Maximum forward velocity
- **Physics:** Higher value = faster top speed

#### `PLAYER_MIN_VELOCITY`
- **Type:** `float`
- **Default:** `-10`
- **Description:** Maximum reverse velocity (negative = backwards)
- **Physics:** More negative = faster reverse

#### `PLAYER_MAX_ANGLE`
- **Type:** `float`
- **Default:** `0.8`
- **Units:** radians
- **Description:** Maximum steering angle (right turn)
- **Conversion:** `0.8 rad ≈ 46°`

#### `PLAYER_MIN_ANGLE`
- **Type:** `float`
- **Default:** `-0.8`
- **Units:** radians
- **Description:** Maximum steering angle (left turn)
- **Conversion:** `-0.8 rad ≈ -46°`

#### `PLAYER_ACCELERATION_FORCE`
- **Type:** `float`
- **Default:** `4`
- **Description:** Acceleration force when "forward" command is active
- **Physics:** Higher = faster acceleration

#### `PLAYER_BRAKE_FORCE`
- **Type:** `float`
- **Default:** `1`
- **Description:** Braking/reverse force when "brake" command is active
- **Physics:** Higher = faster braking/reverse

#### `PLAYER_DRAG_FACTOR`
- **Type:** `float`
- **Default:** `0.5`
- **Description:** Drag coefficient applied to velocity and acceleration
- **Physics:**
  - **Higher (e.g., 0.7)**: More drag, slower top speed, faster deceleration
  - **Lower (e.g., 0.3)**: Less drag, higher top speed, slower deceleration

#### `PLAYER_STEERING_FACTOR`
- **Type:** `float`
- **Default:** `10`
- **Description:** Divisor for steering sensitivity
- **Physics:**
  - **Higher (e.g., 15)**: Less sensitive steering, wider turns
  - **Lower (e.g., 7)**: More sensitive steering, tighter turns

### Collision

#### `COLLISION_THRESHOLD`
- **Type:** `float`
- **Default:** `280`
- **Description:** Distance from road center that triggers collision
- **Physics:** Higher = more forgiving, can drive further off-road

#### `COLLISION_MIN_VELOCITY`
- **Type:** `float`
- **Default:** `5`
- **Description:** Minimum velocity required for collision effect
- **Purpose:** Prevent collision penalties when stationary or slow

## Visual Settings

### `SCREEN_WIDTH`
- **Type:** `int`
- **Default:** `320`
- **Units:** pixels
- **Description:** Virtual screen width for rendering
- **Notes:** Scaled to window size, keeps pixel art aesthetic

### `SCREEN_HEIGHT`
- **Type:** `int`
- **Default:** `180`
- **Units:** pixels
- **Description:** Virtual screen height for rendering
- **Notes:** 16:9 aspect ratio

### `ROAD_DRAW_DISTANCE`
- **Type:** `int`
- **Default:** `120`
- **Description:** How far ahead the road is drawn
- **Performance:**
  - **Higher (e.g., 150)**: More visible road, more CPU usage
  - **Lower (e.g., 90)**: Less visible road, better performance

### `ROAD_PERSPECTIVE_FACTOR`
- **Type:** `int`
- **Default:** `150`
- **Description:** Controls perspective projection strength
- **Visual:**
  - **Higher (e.g., 200)**: Less pronounced perspective
  - **Lower (e.g., 100)**: More pronounced 3D effect

### `ROAD_SCALE_FACTOR`
- **Type:** `int`
- **Default:** `160`
- **Description:** Vertical scaling factor for road rendering
- **Visual:** Affects apparent height of road elements

### `ROAD_BASE_HEIGHT`
- **Type:** `int`
- **Default:** `60`
- **Units:** pixels
- **Description:** Base Y position of horizon line
- **Visual:** Higher = road appears higher on screen

### Road Colors

#### `ROAD_COLOR_BASE`
- **Type:** `tuple[int, int, int]`
- **Default:** `(50, 130, 50)`
- **Format:** RGB (0-255 each)
- **Description:** Base color for road (grass/terrain)
- **Default:** Green grass

#### `ROAD_COLOR_DISTANCE_FACTOR`
- **Type:** `int`
- **Default:** `3`
- **Description:** How much colors fade with distance
- **Visual:** Higher = more dramatic fading

#### `ROAD_COLOR_Z_FACTOR`
- **Type:** `int`
- **Default:** `20`
- **Description:** Color variation based on height (incline)
- **Visual:** Creates depth perception

#### `ROAD_COLOR_SINE_FACTOR`
- **Type:** `int`
- **Default:** `30`
- **Description:** Sinusoidal color variation for texture
- **Visual:** Adds visual variety to terrain

## Road Generation

### Curves

#### `ROAD_CURVE_FREQUENCY_1`
- **Type:** `int`
- **Default:** `17`
- **Description:** Frequency of primary curve oscillation
- **Effect:** Lower = wider, sweeping curves

#### `ROAD_CURVE_AMPLITUDE_1`
- **Type:** `int`
- **Default:** `200`
- **Description:** Amplitude of primary curves
- **Effect:** Higher = sharper turns

#### `ROAD_CURVE_FREQUENCY_2`
- **Type:** `int`
- **Default:** `8`
- **Description:** Frequency of secondary curve oscillation
- **Effect:** Adds complexity to curve pattern

#### `ROAD_CURVE_AMPLITUDE_2`
- **Type:** `int`
- **Default:** `170`
- **Description:** Amplitude of secondary curves
- **Effect:** Fine-tunes curve sharpness

### Inclines

#### `ROAD_INCLINE_FREQUENCY_1`
- **Type:** `int`
- **Default:** `13`
- **Description:** Frequency of primary incline oscillation
- **Effect:** Lower = longer hills

#### `ROAD_INCLINE_AMPLITUDE_1`
- **Type:** `int`
- **Default:** `80`
- **Description:** Amplitude of primary inclines
- **Effect:** Higher = steeper hills

#### `ROAD_INCLINE_FREQUENCY_2`
- **Type:** `int`
- **Default:** `7`
- **Description:** Frequency of secondary incline oscillation
- **Effect:** Adds complexity to terrain

#### `ROAD_INCLINE_AMPLITUDE_2`
- **Type:** `int`
- **Default:** `120`
- **Description:** Amplitude of secondary inclines
- **Effect:** Fine-tunes hill steepness

#### `ROAD_INCLINE_BASE`
- **Type:** `int`
- **Default:** `200`
- **Description:** Base height of road (Z position)
- **Effect:** Adjusts overall elevation

## Configuration Examples

### Quick & Responsive BCI
```python
# Fast response, less stable
CONF_THRESHOLD = 0.50
MAJORITY_K = 3
DEADZONE_SEC = 0.4
WIN_SEC = 1.0
HOP_SEC = 0.5
```

### Stable & Accurate BCI
```python
# Slower response, more stable
CONF_THRESHOLD = 0.70
MAJORITY_K = 7
DEADZONE_SEC = 0.8
WIN_SEC = 2.0
HOP_SEC = 0.5
```

### Performance Mode
```python
# Lower graphics load
ROAD_DRAW_DISTANCE = 90
ROAD_PERSPECTIVE_FACTOR = 180
SCREEN_WIDTH = 320
SCREEN_HEIGHT = 180
```

### Visual Quality Mode
```python
# Better graphics
ROAD_DRAW_DISTANCE = 150
ROAD_PERSPECTIVE_FACTOR = 130
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 270
```

### Easy Driving
```python
# More forgiving physics
PLAYER_MAX_VELOCITY = 15
PLAYER_ACCELERATION_FORCE = 5
PLAYER_DRAG_FACTOR = 0.6
COLLISION_THRESHOLD = 320
```

### Challenging Driving
```python
# More difficult physics
PLAYER_MAX_VELOCITY = 25
PLAYER_ACCELERATION_FORCE = 3
PLAYER_DRAG_FACTOR = 0.3
COLLISION_THRESHOLD = 200
```

## See Also

- [Main Trainer Documentation](README.md)
- [BCI Pipeline Details](BCI_PIPELINE.md)
- [Troubleshooting Guide](README.md#troubleshooting)

