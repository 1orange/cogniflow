# Documentation

This directory contains comprehensive documentation for the Cogniflow project, with a focus on the Emotiv EPOC Gen 1 integration improvements and the integrated ML Pipeline (Modulus).

## 📚 Quick Start

**Start here:** [Emotiv Improvements Quick Start](emotiv/README_IMPROVEMENTS.md)

## 📖 Documentation Index

### Overview Documents

1. **[CHANGELOG.md](CHANGELOG.md)** 📅 **Start Here for What's New**
   - Dated changelog with all project changes
   - Version history
   - Migration guides
   - Future roadmap

2. **[EMOTIV_IMPROVEMENTS.md](EMOTIV_IMPROVEMENTS.md)**
   - Detailed guide to all improvements made
   - API changes and new features
   - Migration guide
   - Troubleshooting

3. **[CHANGES_SUMMARY.md](CHANGES_SUMMARY.md)**
   - Quick before/after comparison
   - Code examples
   - Complete change summary

### Detailed Changelogs

Located in [`changelogs/`](changelogs/) subdirectory:

- **[2025-11-02.md](changelogs/2025-11-02.md)** - Emotiv EPOC Gen 1 Integration Improvements
  - Complete technical details
  - Code examples and migration guides
  - Performance impact analysis

See [changelogs/README.md](changelogs/README.md) for the full index.

### Emotiv EPOC Gen 1 Technical Documentation

Located in [`emotiv/`](emotiv/) subdirectory:

1. **[README_IMPROVEMENTS.md](emotiv/README_IMPROVEMENTS.md)** ⭐ **Start Here**
   - Quick start guide
   - How to build and test
   - Example usage
   - Verification checklist

2. **[PACKET_STRUCTURE.md](emotiv/PACKET_STRUCTURE.md)**
   - Complete packet specification
   - Byte-by-byte breakdown
   - Conversion formulas
   - Technical reference

3. **[VISUAL_PACKET_GUIDE.md](emotiv/VISUAL_PACKET_GUIDE.md)**
   - Visual diagrams and examples
   - Packet parsing walkthrough
   - Signal quality visualization
   - Quick reference cards

## 🎯 What Was Improved

### 1. ✅ Fixed Gyroscope Decryption
- **Before:** Raw bytes (0-255)
- **After:** Signed values (-104 to +151), 0 = neutral
- **Why:** More intuitive for motion detection

### 2. ✅ Added Battery Level
- **Location:** Byte 26
- **Output:** Percentage (0-100%)
- **Use:** Monitor headset power in real-time

### 3. ✅ Added Signal Quality
- **Location:** Bytes 26-28
- **Output:** Quality rating (0-4) per sensor
- **Use:** Check sensor contact before recording

### 4. ✅ Verified Sensor Alignment
- Confirmed perfect alignment with python-emotiv reference
- All 14 EEG sensors correctly decoded

## 🚀 Quick Usage Example

```python
from bci.emotiv import EEGReader

with EEGReader() as reader:
    for packet in reader.read_parsed():
        # NEW: Battery level
        print(f"Battery: {packet.battery}%")
        
        # IMPROVED: Signed gyro (0 = still)
        print(f"Gyro: X={packet.gyro_x}, Y={packet.gyro_y}")
        
        # NEW: Signal quality
        for sensor, quality in packet.quality.items():
            if quality < 3:
                print(f"⚠️  {sensor}: Poor contact")
        
        # EEG data
        print(f"F3: {packet.sensors['F3']}")
        break
```

## 📊 Data Structure

### ParsedPacket Fields

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `counter` | int | 0-255 | Packet sequence number |
| `gyro_x` | int | -104 to +151 | X-axis rotation (signed) |
| `gyro_y` | int | -104 to +151 | Y-axis rotation (signed) |
| `battery` | int | 0-100 | Battery percentage |
| `sensors` | dict | 0-16383 | 14 EEG channels (14-bit values) |
| `quality` | dict | 0-4 | Contact quality per sensor |
| `timestamp` | float | - | Unix timestamp |

### Quality Scale

- **0** (⚫ Black): No signal
- **1** (🔴 Red): Very poor
- **2** (🟠 Orange): Poor
- **3** (🟡 Yellow): Fair
- **4** (🟢 Green): Good

## 🔧 Building the Project

```bash
# Rebuild Rust extension
cd bci/emotiv/lib
bash install_dev.sh

# Run tests
cd /home/jean/dev/diplomka/cogniflow
poetry run python scripts/test_emotiv_rs.py
```

## 📦 Files Modified

### Rust Implementation
- `bci/emotiv/lib/src/lib.rs` - Core implementation with new features

### Python Wrapper
- `bci/emotiv/reader.py` - Updated ParsedPacket dataclass

### Tests
- `scripts/test_emotiv_rs.py` - Enhanced test suite with comprehensive output

## 🎓 Learning Path

1. **Quick Overview**
   - Read: [CHANGES_SUMMARY.md](CHANGES_SUMMARY.md)
   - Time: 5 minutes

2. **Getting Started**
   - Read: [emotiv/README_IMPROVEMENTS.md](emotiv/README_IMPROVEMENTS.md)
   - Build and test the project
   - Time: 15 minutes

3. **Understanding the Protocol**
   - Read: [emotiv/VISUAL_PACKET_GUIDE.md](emotiv/VISUAL_PACKET_GUIDE.md)
   - See packet structure with diagrams
   - Time: 20 minutes

4. **Deep Dive**
   - Read: [emotiv/PACKET_STRUCTURE.md](emotiv/PACKET_STRUCTURE.md)
   - Read: [EMOTIV_IMPROVEMENTS.md](EMOTIV_IMPROVEMENTS.md)
   - Time: 30 minutes

## ✅ Verification Checklist

After building, verify:

- [ ] All tests pass: `poetry run python scripts/test_emotiv_rs.py`
- [ ] Gyro shows ~0 when still (not ~104)
- [ ] Battery shows 0-100 range
- [ ] Quality shows 0-4 per sensor
- [ ] All 14 sensors present in output

With real headset:

- [ ] Battery shows reasonable percentage
- [ ] Quality changes when adjusting sensors
- [ ] Gyro changes when moving head
- [ ] EEG data streams correctly

## 🐛 Troubleshooting

See [EMOTIV_IMPROVEMENTS.md](EMOTIV_IMPROVEMENTS.md#troubleshooting) for:
- Build issues
- Value interpretation
- Hardware-specific quirks

## 🔧 Device Management System

Cogniflow now includes a comprehensive device management system that supports multiple EEG data sources and allows easy switching between devices.

### Supported Devices

1. **🧠 Emotiv EPOC** - Real EEG headset (14 channels, 128 Hz)
   - Automatic detection via HID enumeration
   - Supports multiple connected devices
   - Shows device serial numbers and VID/PID

2. **🔧 Dummy Device** - Simulated data for testing/development
   - Generates synthetic EEG-like signals
   - Includes realistic frequency components (alpha, beta, theta waves)
   - Useful for testing without hardware
   - Configurable noise and artifact levels

### Device Selection

Access the device settings from the main menu:
1. Press `[S]` to open Settings scene
2. Use `[↑/↓]` to navigate available devices
3. Press `[ENTER]` to connect to selected device
4. Press `[R]` to refresh device list
5. Press `[ESC]` to return to menu

### Architecture

The device management system follows a clean architecture:

- **`bci/devices.py`**: Device enumeration and information structures
  - `DeviceType` enum for device types
  - `DeviceInfo` dataclass for device metadata
  - `enumerate_all_devices()` for device discovery

- **`bci/dummy_provider.py`**: Synthetic data generator
  - Threaded data generation matching real device rates
  - Realistic signal characteristics
  - Compatible with existing BCI workflows

- **`trainer/utils/source_manager.py`**: Centralized device management
  - Singleton pattern for global state
  - Automatic device selection fallback
  - Runtime device switching support

- **`trainer/scenes/settings.py`**: Device selection UI
  - MVC architecture (Model-View-Controller)
  - Visual device browser
  - Connection status display

### Usage Example

```python
from trainer.utils.source_manager import source_manager
from bci.devices import enumerate_all_devices

# Enumerate available devices
devices = enumerate_all_devices()
print(f"Found {len(devices)} device(s)")

# Select a device via source manager
if devices:
    source_manager.select_device(devices[0])
    
# Get current data source
source = source_manager.get_source()
if source:
    data = source.read(n_samples=128)
```

### Benefits

- ✅ **No Hardware Required**: Test with dummy device
- ✅ **Multiple Devices**: Support for multiple Emotiv headsets
- ✅ **Easy Switching**: Change devices without restarting
- ✅ **Better Testing**: Dummy device enables CI/CD testing
- ✅ **User-Friendly**: Visual device selection interface

## 🤖 ML Pipeline (Modulus) Documentation

The Cogniflow project now includes an integrated ML Pipeline module called Modulus. For detailed documentation on the ML pipeline:

- **[Modulus Documentation Index](../modulus/docs/INDEX.md)** - Complete ML pipeline documentation
- **[Modulus Quick Start](modulus/QUICKSTART.md)** - Get started with ML pipeline
- **[Experiment Features](modulus/EXPERIMENT_FEATURES.md)** ⭐ **NEW** - Comprehensive experiment system guide
- **[Modulus System Design](../modulus/SDD.md)** - Architecture and design principles
- **[Modulus Configuration Guide](../modulus/docs/preprocessing-modes.md)** - Configuration options

### Using Modulus from Cogniflow

The Modulus ML Pipeline is accessible through the main menu:
1. Launch Cogniflow: `poetry run python -m trainer.main`
2. Press `[M]` to enter ModulusScene
3. Configure experiments:
   - `[UP]/[DOWN]` - Select experiment mode (Binary/Multiclass/Both)
   - `[Q]` - Toggle Quick Mode
   - `[H]` - Toggle Hyperparameter Tuning
4. Press `[ENTER]` to run experiments
5. View results in `results/experiments_{mode}_{timestamp}/`
6. Load saved models from `models/` folder

**New Features:**
- ✅ **Split Ratio Testing**: Automatically tests 70/15/15 and 80/10/10 splits
- ✅ **Hyperparameter Tuning**: GridSearchCV optimization for all models
- ✅ **Model Persistence**: All trained models saved to `models/` folder
- ✅ **Interactive UI**: Configure and run experiments through Pygame interface

The ModulusScene follows MVC architecture and integrates seamlessly with the Cogniflow interface.

## 📚 References

- [python-emotiv](https://github.com/ozancaglayan/python-emotiv) - Reference implementation
- [Emotiv EPOC User Manual](https://s.paszkiel.po.edu.pl/wp-content/uploads/2016/01/EPOCUserManual2014.pdf)
- [emokit library](https://github.com/openyou/emokit) - Original reverse engineering

## 📝 License

See project root for license information.

---

**Questions?** All documentation is self-contained in this `docs/` directory and `modulus/docs/` directory. Start with the Quick Start guide and work through the materials as needed.

