# Changelog

All notable changes to the Cogniflow project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## 📅 Detailed Changelogs by Date

For complete, detailed changelogs organized by date, see the **[changelogs/](changelogs/)** directory:

- **[2025-11-02.md](changelogs/2025-11-02.md)** - Emotiv EPOC Gen 1 Integration Improvements (detailed)

Each dated changelog contains comprehensive information including:
- Detailed technical implementation
- Code examples and comparisons
- Migration guides
- Known issues and workarounds
- Performance impact analysis

**Below is a condensed overview. For full details, see the dated files.**

---

## [Unreleased]

### Planned
- Neural network model implementation for BCI classification
- Real-time performance monitoring dashboard
- Multi-session calibration data aggregation
- Advanced signal quality visualization

---

## [2025-11-02] - Emotiv EPOC Gen 1 Integration Improvements

### Added

#### Battery Level Monitoring
- Added battery level decryption from Emotiv EPOC packets (byte 26)
- Battery reported as percentage (0-100%)
- Proper integer overflow handling in battery calculation
- Battery status now available in all parsed packets via `parsed['battery']`

#### Signal Quality Detection
- Added contact quality measurement for all 14 EEG sensors
- Quality values on 0-4 scale:
  - 0 = No signal (sensor not touching)
  - 1 = Very poor contact (needs adjustment)
  - 2 = Poor contact (unusable)
  - 3 = Fair contact (marginal)
  - 4 = Good contact (ideal for recording)
- Quality extracted from bytes 26-28 using nibble packing
- Quality data available as `parsed['quality']` dictionary
- Visual indicators with emoji labels in test output

#### Documentation
- Created comprehensive documentation structure in `docs/` folder
- Added `docs/README.md` as main documentation hub
- Created `docs/emotiv/` subdirectory for Emotiv-specific docs:
  - `PACKET_STRUCTURE.md` - Technical packet specification
  - `VISUAL_PACKET_GUIDE.md` - Visual diagrams and examples
  - `README_IMPROVEMENTS.md` - Quick start guide
- Created `docs/trainer/` subdirectory for trainer documentation:
  - `README.md` - Complete trainer guide
  - `CONFIGURATION.md` - Configuration reference
- Added `EMOTIV_IMPROVEMENTS.md` - Detailed improvements guide
- Added `CHANGES_SUMMARY.md` - Quick before/after comparison

### Fixed

#### Gyroscope Data Conversion
- **Issue**: Gyroscope returned raw unsigned bytes (0-255), difficult to interpret
- **Fix**: Converted to signed values relative to neutral position (104)
- **Before**: `gyro_x = packet[29]` (returns 104 when still)
- **After**: `gyro_x = packet[29] as i16 - 104` (returns 0 when still)
- Gyro now returns intuitive values: -104 to +151 range
- Zero indicates neutral/stable head position
- Positive/negative values clearly indicate movement direction

#### Array Bounds Error in Quality Extraction
- **Issue**: Index out of bounds panic when accessing byte 32 in quality extraction
- **Fix**: Added bounds checking to prevent array access beyond packet size
- Sensors beyond available quality data now default to quality 0
- Prevents crash when processing edge-case packets

#### Battery Calculation Integer Overflow
- **Issue**: Battery showed 4% instead of expected 41% due to u8 overflow
- **Problem**: `(220 - 200) * 100` = 2000, which doesn't fit in u8 (max 255)
- **Fix**: Cast to u16 before multiplication to prevent overflow
- **Result**: Battery percentages now calculate correctly

### Changed

#### Python API - ParsedPacket Dataclass
- **Before**:
  ```python
  @dataclass
  class ParsedPacket:
      counter: int
      gyro_x: int      # Raw 0-255
      gyro_y: int      # Raw 0-255
      sensors: Dict[str, int]
      timestamp: float
  ```

- **After**:
  ```python
  @dataclass
  class ParsedPacket:
      counter: int
      gyro_x: int                  # Signed -104 to +151
      gyro_y: int                  # Signed -104 to +151
      battery: int                 # NEW: 0-100%
      sensors: Dict[str, int]
      quality: Dict[str, int]      # NEW: 0-4 per sensor
      timestamp: float
  ```

#### Rust API - parse_sensor_data_impl
- **Before**: Returns `(counter, gyro_x, gyro_y, sensors)`
- **After**: Returns `(counter, gyro_x, gyro_y, battery, sensors, qualities)`
- Added battery extraction with proper percentage conversion
- Added quality extraction for all 14 sensors
- Improved gyro conversion to signed integers

#### Test Suite Enhancement
- Enhanced `test_emotiv_rs.py` with comprehensive output
- Added realistic packet simulation (Test 4b) with varied data
- Now displays all 14 sensor values (previously only first 3)
- Now displays all 14 quality values with emoji labels
- Better explanations of expected vs actual values
- Added battery percentage display and verification

### Verified

#### Sensor Data Alignment
- Confirmed perfect alignment with python-emotiv reference implementation
- Counter position (byte 0) ✓
- 14 EEG sensors with 14-bit packing (bytes 1-25) ✓
- Sensor names and order match ✓
- Gyro position (bytes 29-30) ✓
- AES decryption key matches ✓
- Bit extraction order (LSB first) ✓

### Technical Details

#### Files Modified
- `bci/emotiv/lib/src/lib.rs` - Core Rust implementation
  - Added `get_quality_impl()` function
  - Enhanced `parse_sensor_data_impl()` with new fields
  - Fixed gyro conversion logic
  - Added battery extraction with overflow protection
  - Added bounds checking for quality extraction

- `bci/emotiv/reader.py` - Python wrapper
  - Updated `ParsedPacket` dataclass with new fields
  - Modified `read_parsed()` to include battery and quality
  - Updated `record()` to save new data fields

- `test_emotiv_rs.py` - Test suite
  - Enhanced sensor parsing test with dual test cases
  - Added comprehensive output for all sensors and quality values
  - Added realistic packet simulation with varied data

#### Packet Structure Clarification
- Battery: Byte 26 (raw 200-248 typical, converted to 0-100%)
- Quality: Bytes 26-28 (nibble-packed, 4 bits per sensor)
- Gyro X: Byte 29 (converted to signed: raw - 104)
- Gyro Y: Byte 30 (converted to signed: raw - 104)

---

## [2025-10-05] - Previous Changes

### Data Recording
- Removed old recorded data files:
  - `data/metadata_forward_20251005_223350.txt`
  - `data/recorded_data_forward_20251005_223350.npy`

### Known Issues
- Gyro decryption was incorrect (returned raw bytes)
- Battery level not available
- Signal quality not available
- Integer overflow in battery calculation (if implemented)

---

## Project History

### Initial Development

#### Emotiv EPOC Integration
- Rust-based USB reader implementation using hidapi
- AES-128 ECB decryption for Emotiv packets
- PyO3 Python bindings for Rust reader
- 14-channel EEG sensor data extraction with bit-packing
- Support for Emotiv EPOC Gen 1 (2013 model)

#### BCI Trainer Application
- Pygame-based interactive training application
- Multiple scenes:
  - Menu scene for navigation
  - Calibration scene for BCI model training
  - Record scene for raw data collection
  - Driving scene for BCI-controlled gameplay
- Pseudo-3D racing environment
- Real-time EEG signal processing
- Asynchronous BCI pipeline for smooth 60 FPS
- Support for both BCI and keyboard control modes

#### Signal Processing
- Configurable bandpass filtering (1-40 Hz default)
- Notch filter for power line interference (50/60 Hz)
- Artifact rejection based on amplitude threshold
- Sliding window processing with configurable overlap
- Multi-band power spectral density features
- Majority voting for prediction stability

#### Project Structure
- Modular architecture with separate BCI and trainer modules
- Centralized configuration in `config.py`
- Asset management for sprites and textures
- Utility modules for car physics and source management
- Data storage in NumPy format with metadata

---

## Migration Guide

### From Previous Version (Before 2025-11-02)

If you have existing code using the old API:

#### 1. Update ParsedPacket Usage

**Before**:
```python
packet = reader.poll_parsed()
print(f"Gyro: {packet.gyro_x}, {packet.gyro_y}")  # Raw 0-255
```

**After**:
```python
packet = reader.poll_parsed()
print(f"Gyro: {packet.gyro_x}, {packet.gyro_y}")  # Signed -104 to +151
print(f"Battery: {packet.battery}%")              # NEW
print(f"Quality: {packet.quality}")               # NEW
```

#### 2. Interpret Gyro Values

**Before**: `gyro_x = 104` meant neutral
**After**: `gyro_x = 0` means neutral

```python
# Check if head is stable
if abs(packet.gyro_x) < 5 and abs(packet.gyro_y) < 5:
    print("Head stable")
```

#### 3. Use New Features

```python
# Monitor battery
if packet.battery < 20:
    print("Low battery!")

# Check signal quality before recording
poor_sensors = [s for s, q in packet.quality.items() if q < 3]
if poor_sensors:
    print(f"Poor contact: {poor_sensors}")
```

#### 4. Rebuild Rust Extension

```bash
cd bci/emotiv/lib
bash install_dev.sh
```

#### 5. Run Tests

```bash
poetry run python test_emotiv_rs.py
```

All tests should pass with new battery and quality fields visible.

---

## Compatibility Notes

### Backward Compatibility
- **Breaking Changes**: Yes
  - Gyro values now signed (0 = neutral instead of ~104)
  - ParsedPacket has new required fields (battery, quality)
  - parse_sensor_data_impl() return type changed

### Emotiv EPOC Compatibility
- **Tested**: Emotiv EPOC Gen 1 (2013 model)
- **AES Key**: `31003554381037423100354838003750`
- **Packet Size**: 32 bytes
- **Sample Rate**: 128 Hz
- **Channels**: 14 (F3, FC5, AF3, F7, T7, P7, O1, O2, P8, T8, FC6, F4, F8, AF4)

### Firmware Variations
- Battery encoding may vary between firmware versions
- Quality encoding may differ in some Gen 1 units
- Typical battery range: 200-248 (raw values)
- Quality nibble packing may vary

---

## Acknowledgments

### References
- [python-emotiv](https://github.com/ozancaglayan/python-emotiv) - Reference implementation
- [emokit](https://github.com/openyou/emokit) - Original reverse engineering
- [Emotiv EPOC User Manual](https://s.paszkiel.po.edu.pl/wp-content/uploads/2016/01/EPOCUserManual2014.pdf)

### Tools & Libraries
- **Rust**: hidapi, aes, pyo3, crossbeam
- **Python**: pygame, numpy, scipy
- **Poetry**: Dependency management
- **Maturin**: Rust-Python binding builder

---

## Future Roadmap

### Short Term
- [ ] Implement actual ML model training in calibration
- [ ] Add real-time BCI accuracy monitoring
- [ ] Create signal quality visualization widget
- [ ] Add session recording and replay

### Medium Term
- [ ] Support for Emotiv EPOC+ (newer model)
- [ ] Advanced preprocessing pipeline
- [ ] Multi-user calibration profiles
- [ ] Performance analytics dashboard

### Long Term
- [ ] Deep learning models for BCI classification
- [ ] Adaptive calibration
- [ ] Multi-modal BCI (EEG + other sensors)
- [ ] Cloud-based model training

---

## Contributing

See main project README for contribution guidelines.

## License

See project root for license information.

---

**Last Updated**: 2025-11-02  
**Document Version**: 1.0  
**Project Version**: 0.2.0 (post-Emotiv improvements)

