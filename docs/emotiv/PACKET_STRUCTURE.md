# Emotiv EPOC Gen 1 Packet Structure

This document describes the data packet structure for the Emotiv EPOC Gen 1 headset (2013 model) after AES decryption.

## Overview

After USB communication and AES-128 decryption, each packet is **32 bytes** containing:
- Sequence counter
- 14 EEG sensor readings (14-bit each)
- Battery level
- Contact quality for each sensor
- 2-axis gyroscope data

## Packet Layout (After Decryption)

| Byte(s) | Field | Description |
|---------|-------|-------------|
| 0 | Counter | Sequence number (0-255, wraps around) |
| 1-25 | EEG Sensors | 14 sensors × 14 bits (packed), see sensor mapping below |
| 26 | Battery | Battery level (raw: 200-248, converted to 0-100%) |
| 26-28 | Quality | Contact quality packed in nibbles (4 bits per sensor) |
| 29 | Gyro X | Gyroscope X-axis (raw 0-255, neutral ~104) |
| 30 | Gyro Y | Gyroscope Y-axis (raw 0-255, neutral ~104) |
| 31 | Reserved | Unused |

## EEG Sensor Mapping (14 channels)

The 14 EEG sensors are mapped according to the 10-20 system:

| Sensor | Location | Bits in Packet |
|--------|----------|----------------|
| F3 | Left frontal | Bytes 0-2 (14 bits starting at byte 0, bit 6) |
| FC5 | Left frontal-central | Bytes 2-4 |
| AF3 | Left anterior frontal | Bytes 4-5 |
| F7 | Left frontal-temporal | Bytes 6-7 |
| T7 | Left temporal | Bytes 7-9 |
| P7 | Left parietal | Bytes 9-11 |
| O1 | Left occipital | Bytes 11-12 |
| O2 | Right occipital | Bytes 13-14 |
| P8 | Right parietal | Bytes 14-16 |
| T8 | Right temporal | Bytes 16-18 |
| FC6 | Right frontal-central | Bytes 18-19 |
| F4 | Right frontal | Bytes 20-21 |
| F8 | Right frontal-temporal | Bytes 21-23 |
| AF4 | Right anterior frontal | Bytes 23-25 |

Each sensor value is 14 bits (0-16383), representing the voltage level at that electrode.

## Battery Level

- **Byte**: 26
- **Raw Range**: 200-248 (typical operating range)
- **Converted**: 0-100%
- **Conversion Formula**: 
  ```
  if raw > 248: battery = 100%
  elif raw < 200: battery = 0%
  else: battery = ((raw - 200) * 100 / 48)%
  ```

## Contact Quality

Contact quality indicates how well each sensor is making contact with the scalp:

- **Bytes**: 26-28 (overlaps with battery in byte 26, uses different bits)
- **Encoding**: 4 bits per sensor (nibbles)
- **Values**: 0-4 (clamped from potential 0-15 range)

| Value | Quality | Color Code | Meaning |
|-------|---------|------------|---------|
| 0 | No signal | Black | Sensor not connected |
| 1 | Very poor | Red | Very poor contact |
| 2 | Poor | Orange | Poor contact, unusable |
| 3 | Fair | Yellow | Fair contact, marginal |
| 4 | Good | Green | Good contact, ideal |

### Quality Extraction

The 14 sensors' quality values are packed in bytes 26-28:
- Sensor 0 (F3): Byte 26, lower nibble (bits 0-3)
- Sensor 1 (FC5): Byte 26, upper nibble (bits 4-7)
- Sensor 2 (AF3): Byte 27, lower nibble (bits 0-3)
- ... and so on

## Gyroscope Data

The Emotiv EPOC Gen 1 includes a 2-axis gyroscope (IDG500) with ±8g range.

- **Byte 29**: Gyro X-axis
- **Byte 30**: Gyro Y-axis
- **Raw Range**: 0-255 (unsigned byte)
- **Neutral Position**: ~104 (when headset is still)
- **Converted Range**: -104 to +151 (signed, relative to neutral)

### Gyro Conversion

```rust
let gyro_x_raw = packet[29] as i16;
let gyro_y_raw = packet[30] as i16;

// Convert to signed values relative to neutral (104)
let gyro_x = gyro_x_raw - 104;  // -104 to +151
let gyro_y = gyro_y_raw - 104;  // -104 to +151
```

When the headset is stationary, gyro values should be near 0 (±2).
Positive values indicate movement in one direction, negative in the opposite.

## AES Decryption

The raw USB packets are encrypted with AES-128 ECB:

- **Key (hex)**: `31003554381037423100354838003750`
- **Algorithm**: AES-128 ECB mode
- **Block Size**: 16 bytes (decrypt two blocks per 32-byte packet)

## Example Usage

### Python (using emotiv_rs)

```python
from emotiv_rs import EmotivReader

reader = EmotivReader(None, None, None, None)  # Use defaults
reader.start()

try:
    while True:
        parsed = reader.poll_parsed()
        if parsed:
            print(f"Counter: {parsed['counter']}")
            print(f"Battery: {parsed['battery']}%")
            print(f"Gyro: X={parsed['gyro_x']}, Y={parsed['gyro_y']}")
            
            # Print sensor values
            for name, value in parsed['sensors'].items():
                quality = parsed['quality'][name]
                print(f"{name}: {value} (quality: {quality})")
finally:
    reader.stop()
```

### Using the High-Level API

```python
from bci.emotiv import EEGReader

with EEGReader() as reader:
    for packet in reader.read_parsed():
        print(f"Counter: {packet.counter}")
        print(f"Battery: {packet.battery}%")
        print(f"Gyro: X={packet.gyro_x}, Y={packet.gyro_y}")
        
        # Access sensor data
        f3_value = packet.sensors['F3']
        f3_quality = packet.quality['F3']
        
        print(f"F3: {f3_value} (quality: {f3_quality})")
```

## Alignment with python-emotiv

This implementation is aligned with the [python-emotiv](https://github.com/ozancaglayan/python-emotiv) project:

1. **Sensor Mapping**: Same 14-bit packed structure for EEG sensors
2. **Gyro Position**: Bytes 29-30 (matches python-emotiv)
3. **Counter**: Byte 0 (matches python-emotiv)
4. **Battery**: Byte 26 (standard EPOC Gen 1 location)
5. **Quality**: Bytes 26-28 (standard EPOC Gen 1 encoding)

### Improvements Over Raw Gyro

Unlike the original python-emotiv which returns raw gyro bytes (0-255), this implementation:
- Converts to signed integers relative to neutral position
- Makes gyro values more intuitive (0 = still, +/- = movement direction)
- Provides better compatibility with motion analysis algorithms

## References

- [python-emotiv GitHub](https://github.com/ozancaglayan/python-emotiv)
- [Emotiv EPOC User Manual (2014)](https://s.paszkiel.po.edu.pl/wp-content/uploads/2016/01/EPOCUserManual2014.pdf)
- [emokit library](https://github.com/openyou/emokit) - Original reverse engineering work

## Notes

- The quality encoding may vary slightly between firmware versions
- Battery percentage is approximate and based on typical operating voltages
- Gyro neutral position (104) may vary slightly between devices (102-106)
- Some Gen 1 devices may use different encryption keys

