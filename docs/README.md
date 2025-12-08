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

