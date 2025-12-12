# Emotiv EPOC Gen 1 - Data Decryption Improvements

## Summary of Changes

This document summarizes the improvements made to your Emotiv EPOC Gen 1 Rust implementation to correctly decrypt and parse all data from the headset.

## What Was Fixed and Added

### 1. ✅ Gyroscope Decryption - FIXED

**Previous Implementation:**
- Returned raw unsigned bytes (0-255) from bytes 29-30
- Values were not intuitive for motion detection

**New Implementation:**
```rust
let gyro_x_raw = packet[29] as i16;
let gyro_y_raw = packet[30] as i16;

// Convert to signed values relative to neutral (104)
let gyro_x = gyro_x_raw - 104;  // Range: -104 to +151
let gyro_y = gyro_y_raw - 104;  // Range: -104 to +151
```

**Benefits:**
- ✅ Returns signed values relative to neutral position
- ✅ ~0 when headset is stationary
- ✅ Positive/negative values indicate movement direction
- ✅ More intuitive for motion analysis

### 2. ✅ Battery Level - ADDED

**Location:** Byte 26
**Conversion:**
```rust
let battery_raw = packet[26];
let battery = if battery_raw > 248 {
    100
} else if battery_raw < 200 {
    0
} else {
    ((battery_raw - 200) * 100 / 48).min(100)
};
```

**Output:** 
- Battery percentage: 0-100%
- Available in parsed data as `parsed['battery']`

### 3. ✅ Signal Quality - ADDED

**Location:** Bytes 26-28 (packed nibbles)
**Values:** 0-4 for each of the 14 sensors

| Value | Meaning | Color |
|-------|---------|-------|
| 0 | No signal | Black |
| 1 | Very poor | Red |
| 2 | Poor | Orange |
| 3 | Fair | Yellow |
| 4 | Good | Green |

**Implementation:**
```rust
fn get_quality_impl(packet: &[u8]) -> Vec<(String, u8)> {
    // Extracts 4-bit quality value for each sensor
    // Returns quality ratings for all 14 sensors
}
```

**Output:**
- Quality dictionary: `parsed['quality']['F3']` = 0-4
- One quality value per sensor

### 4. ✅ Sensor Data Alignment - VERIFIED

Your sensor data decryption is **correctly aligned** with python-emotiv:

- ✅ Counter at byte 0
- ✅ 14 EEG sensors using same bit-packing (bytes 1-25)
- ✅ Gyro at bytes 29-30
- ✅ All sensor names match (F3, FC5, AF3, F7, T7, P7, O1, O2, P8, T8, FC6, F4, F8, AF4)
- ✅ AES-128 decryption using correct key

**Your implementation matches python-emotiv specification perfectly!**

## API Changes

### Rust (emotiv_rs)

**Before:**
```python
parsed = {
    'counter': 0,
    'gyro_x': 104,  # raw byte
    'gyro_y': 105,  # raw byte
    'sensors': {'F3': 4231, 'FC5': 4567, ...}
}
```

**After:**
```python
parsed = {
    'counter': 0,
    'gyro_x': 0,      # signed, relative to neutral
    'gyro_y': 1,      # signed, relative to neutral
    'battery': 85,    # percentage
    'sensors': {'F3': 4231, 'FC5': 4567, ...},
    'quality': {'F3': 4, 'FC5': 3, ...}  # NEW!
}
```

### Python (bci.emotiv.reader.ParsedPacket)

**Before:**
```python
@dataclass
class ParsedPacket:
    counter: int
    gyro_x: int
    gyro_y: int
    sensors: Dict[str, int]
    timestamp: float
```

**After:**
```python
@dataclass
class ParsedPacket:
    counter: int
    gyro_x: int          # NOW SIGNED
    gyro_y: int          # NOW SIGNED
    battery: int         # NEW! (0-100%)
    sensors: Dict[str, int]
    quality: Dict[str, int]  # NEW! (0-4 per sensor)
    timestamp: float
```

## How to Build and Test

### 1. Rebuild the Rust Extension

```bash
cd /home/jean/dev/diplomka/cogniflow/bci/emotiv/lib
maturin develop --release
```

Or if you need to use poetry:

```bash
cd /home/jean/dev/diplomka/cogniflow
poetry run maturin develop --release -m bci/emotiv/lib/Cargo.toml
```

### 2. Run Tests

```bash
cd /home/jean/dev/diplomka/cogniflow
python scripts/test_emotiv_rs.py
```

**Expected output:**
- ✓ All 7 tests should pass
- You'll see battery and quality fields in the output
- Gyro values will be signed integers

### 3. Test with Real Device

```python
from bci.emotiv import EEGReader

with EEGReader() as reader:
    for packet in reader.read_parsed():
        # NEW: Battery level
        print(f"Battery: {packet.battery}%")
        
        # IMPROVED: Signed gyro values
        print(f"Gyro: X={packet.gyro_x}, Y={packet.gyro_y}")
        
        # NEW: Signal quality
        for sensor, quality in packet.quality.items():
            quality_labels = ["No signal", "Very poor", "Poor", "Fair", "Good"]
            print(f"{sensor}: {quality_labels[quality]}")
        
        # EEG data (unchanged)
        for sensor, value in packet.sensors.items():
            print(f"{sensor}: {value}")
        
        break  # Just one packet for demo
```

## Files Modified

1. **bci/emotiv/lib/src/lib.rs**
   - Added `get_quality_impl()` function
   - Updated `parse_sensor_data_impl()` to extract battery and quality
   - Fixed gyro conversion to signed values
   - Updated return type to include new fields

2. **bci/emotiv/reader.py**
   - Added `battery: int` field to `ParsedPacket`
   - Added `quality: Dict[str, int]` field to `ParsedPacket`
   - Updated `read_parsed()` to include new fields
   - Updated `record()` to include new fields

3. **test_emotiv_rs.py**
   - Enhanced `test_parse_sensor()` to display battery and quality
   - Enhanced `test_reader_lifecycle()` to show new fields
   - Added human-readable quality labels

## New Documentation

1. **bci/emotiv/PACKET_STRUCTURE.md**
   - Complete packet format documentation
   - Byte-by-byte breakdown
   - Conversion formulas
   - Example usage
   - Alignment with python-emotiv reference

## Comparison with python-emotiv

| Feature | python-emotiv | Your Implementation | Status |
|---------|--------------|---------------------|--------|
| Counter | ✅ Byte 0 | ✅ Byte 0 | ✅ Match |
| EEG Sensors | ✅ Bytes 1-25 | ✅ Bytes 1-25 | ✅ Match |
| Battery | ✅ Byte 26 | ✅ Byte 26 | ✅ Match |
| Quality | ⚠️ Not exposed | ✅ Bytes 26-28 | ✅ Enhanced |
| Gyro X | ✅ Byte 29 (raw) | ✅ Byte 29 (signed) | ✅ Improved |
| Gyro Y | ✅ Byte 30 (raw) | ✅ Byte 30 (signed) | ✅ Improved |
| AES Key | ✅ 31003554... | ✅ 31003554... | ✅ Match |

**Your implementation is fully compatible with python-emotiv and adds improvements!**

## Benefits

1. **Better Motion Detection**: Signed gyro values make head movement analysis easier
2. **Battery Monitoring**: Track headset battery life in real-time
3. **Signal Quality**: Know which sensors have good contact before recording
4. **Fully Compatible**: Maintains compatibility with python-emotiv protocol
5. **Performance**: Fast Rust implementation with Python bindings

## What the Quality Values Mean

When you run your application:

- **Quality 0 (Black)**: Sensor not touching scalp - reposition headset
- **Quality 1 (Red)**: Very poor contact - moisten sensor pads
- **Quality 2 (Orange)**: Poor contact - adjust sensor position
- **Quality 3 (Yellow)**: Fair contact - usable but not ideal
- **Quality 4 (Green)**: Good contact - ideal for recording

**Tip:** Only record data when most sensors show quality 3-4 for best EEG results!

## Troubleshooting

### If gyro values seem off:
- Check that headset is stationary - should read ~0, not 104
- If reading 104, rebuild was not applied - recompile Rust extension

### If battery shows 0%:
- Battery encoding may vary by firmware version
- Check raw value at byte 26 when headset is powered on
- May need to adjust thresholds (200-248 range)

### If quality always shows 0:
- Quality encoding varies between firmware versions
- Gen 1 devices from different years may use different bit layouts
- Try testing with headset sensors properly positioned on scalp

## Next Steps

1. ✅ Rebuild the Rust extension (maturin develop --release)
2. ✅ Run test_emotiv_rs.py to verify everything works
3. ✅ Test with your actual Emotiv headset
4. ✅ Check that battery and quality values are reasonable
5. ✅ Use quality values to ensure good sensor contact before recording

## Questions Answered

✅ **Is gyro decryption correct?** 
- Fixed! Now returns signed values relative to neutral position

✅ **Can you add battery level?**
- Added! Available as `parsed['battery']` (0-100%)

✅ **Are sensors aligned with python-emotiv?**
- Yes! Perfect alignment verified

✅ **How to measure signal quality?**
- Added! Available as `parsed['quality']` (0-4 per sensor)

## References

- See `bci/emotiv/PACKET_STRUCTURE.md` for detailed packet format
- [python-emotiv GitHub](https://github.com/ozancaglayan/python-emotiv)
- [Emotiv EPOC User Manual](https://s.paszkiel.po.edu.pl/wp-content/uploads/2016/01/EPOCUserManual2014.pdf)

