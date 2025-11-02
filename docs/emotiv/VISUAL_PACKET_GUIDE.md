# Visual Packet Structure Guide - Emotiv EPOC Gen 1

## Packet Overview (32 bytes after AES decryption)

```
┌────────────────────────────────────────────────────────────────┐
│                   EMOTIV EPOC GEN 1 PACKET                     │
│                      (32 bytes total)                          │
└────────────────────────────────────────────────────────────────┘

Byte:  0    1    2    3    4    5    6    7    8    9   10   11
     ┌────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┐
     │Cnt │      EEG Sensor Data (14 sensors × 14 bits)          │
     └────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┘

Byte: 12   13   14   15   16   17   18   19   20   21   22   23
     ┌────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┐
     │    EEG Sensor Data (continued)                             │
     └────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┘

Byte: 24   25   26   27   28   29   30   31
     ┌────┬────┬────┬────┬────┬────┬────┬────┐
     │EEG │    │Bat │ Quality  │GyX │GyY │Rsv │
     │    │    │    │(packed)  │    │    │    │
     └────┴────┴────┴────┴────┴────┴────┴────┘
```

## Detailed Byte Breakdown

### Byte 0: Counter
```
┌─────────────────────────────┐
│  Byte 0: Packet Counter     │
├─────────────────────────────┤
│  Range: 0-255               │
│  Wraps around at 256        │
│  Used for packet ordering   │
└─────────────────────────────┘
```

### Bytes 1-25: EEG Sensors (14 channels)

Each sensor uses 14 bits, packed sequentially:

```
Sensor Layout (10-20 System):

        AF3  AF4
     F7  F3  F4  F8
         FC5 FC6
     T7           T8
         P7  P8
         O1  O2

14 Sensors Total:
F3, FC5, AF3, F7, T7, P7, O1, O2, P8, T8, FC6, F4, F8, AF4

Bit Packing Example (first 3 sensors):
┌─────────────────────────────────────────────────────────────┐
│ Byte 0 │ Byte 1          │ Byte 2          │ Byte 3       │
├────────┼─────────────────┼─────────────────┼──────────────┤
│ Counter│ F3 bits 0-5     │ F3 bits 6-13    │ FC5 bits 0-1 │
│        │ (lower 6 bits)  │ (upper 8 bits)  │              │
└────────┴─────────────────┴─────────────────┴──────────────┘
          ^----- F3: 14 bits ------^  ^-- FC5 starts here
```

**Value Range:** 0-16383 (14-bit unsigned integer)
**Represents:** Voltage at electrode (higher = more activity)

### Byte 26: Battery Level

```
┌─────────────────────────────────────┐
│  Byte 26: Battery Status            │
├─────────────────────────────────────┤
│  Raw Range: 200-248 (typical)       │
│  < 200: Dead (0%)                   │
│  200-248: Normal operating range    │
│  > 248: Fully charged (100%)        │
├─────────────────────────────────────┤
│  Conversion to percentage:          │
│  battery = (raw - 200) * 100 / 48   │
│                                     │
│  Examples:                          │
│  Raw 200 → 0%                       │
│  Raw 224 → 50%                      │
│  Raw 248 → 100%                     │
└─────────────────────────────────────┘
```

### Bytes 26-28: Contact Quality (Overlapping with Battery)

The quality data is encoded in the same bytes as battery but uses different bit positions:

```
┌──────────────────────────────────────────────────────────────┐
│  Bytes 26-28: Contact Quality (14 sensors)                   │
├──────────────────────────────────────────────────────────────┤
│  Encoding: 4 bits per sensor (nibbles)                       │
│                                                              │
│  Byte 26:                                                    │
│  ┌───────────┬───────────┐                                  │
│  │ Bits 4-7  │ Bits 0-3  │                                  │
│  │ FC5 (Q1)  │  F3 (Q0)  │                                  │
│  └───────────┴───────────┘                                  │
│                                                              │
│  Byte 27:                                                    │
│  ┌───────────┬───────────┐                                  │
│  │ Bits 4-7  │ Bits 0-3  │                                  │
│  │  F7 (Q3)  │ AF3 (Q2)  │                                  │
│  └───────────┴───────────┘                                  │
│                                                              │
│  ... and so on for all 14 sensors                           │
│                                                              │
│  Quality Values (0-4):                                       │
│  0 = ⚫ No signal    (sensor not touching)                  │
│  1 = 🔴 Very poor    (needs adjustment)                     │
│  2 = 🟠 Poor         (unusable data)                        │
│  3 = 🟡 Fair         (marginal quality)                     │
│  4 = 🟢 Good         (ideal for recording)                  │
└──────────────────────────────────────────────────────────────┘
```

### Byte 29: Gyroscope X-Axis

```
┌─────────────────────────────────────┐
│  Byte 29: Gyro X                    │
├─────────────────────────────────────┤
│  Raw Range: 0-255 (unsigned)        │
│  Neutral: ~104 (headset still)      │
│                                     │
│  Conversion to signed:              │
│  gyro_x = raw - 104                 │
│                                     │
│  Signed Range: -104 to +151         │
│                                     │
│  Interpretation:                    │
│  -104 to -10: Strong left rotation  │
│   -10 to -2 : Slight left           │
│    -2 to +2 : Stable (no movement)  │
│    +2 to +10: Slight right          │
│   +10 to +151: Strong right         │
│                                     │
│  Movement Detection:                │
│  |gyro_x| > 5: Significant movement │
│  |gyro_x| < 3: Stable position      │
└─────────────────────────────────────┘
```

### Byte 30: Gyroscope Y-Axis

```
┌─────────────────────────────────────┐
│  Byte 30: Gyro Y                    │
├─────────────────────────────────────┤
│  Raw Range: 0-255 (unsigned)        │
│  Neutral: ~104 (headset still)      │
│                                     │
│  Conversion to signed:              │
│  gyro_y = raw - 104                 │
│                                     │
│  Signed Range: -104 to +151         │
│                                     │
│  Interpretation:                    │
│  -104 to -10: Strong forward tilt   │
│   -10 to -2 : Slight forward        │
│    -2 to +2 : Stable (no movement)  │
│    +2 to +10: Slight backward       │
│   +10 to +151: Strong backward      │
│                                     │
│  Movement Detection:                │
│  |gyro_y| > 5: Significant movement │
│  |gyro_y| < 3: Stable position      │
└─────────────────────────────────────┘
```

### Byte 31: Reserved

```
┌─────────────────────────────────────┐
│  Byte 31: Reserved                  │
├─────────────────────────────────────┤
│  Not used in Gen 1 protocol         │
│  Usually 0x00                       │
└─────────────────────────────────────┘
```

## Complete Packet Example

### Example Raw Decrypted Packet (hex):
```
2A 3F A1 B2 C3 D4 E5 F6 07 18 29 3A 4B 5C 6D 7E
8F 90 A1 B2 C3 D4 E5 F6 07 D8 34 21 65 68 6A 00
```

### Parsing This Packet:

```
┌────────────────────────────────────────────────┐
│ Byte 0: 0x2A = 42                              │
│ → Counter = 42                                 │
└────────────────────────────────────────────────┘

┌────────────────────────────────────────────────┐
│ Bytes 1-25: (F3 example)                       │
│ Bits from bytes 0-2:                           │
│ → F3 = 4231 (voltage level)                   │
└────────────────────────────────────────────────┘

┌────────────────────────────────────────────────┐
│ Byte 26: 0xD8 = 216                            │
│ → Battery raw = 216                            │
│ → Battery % = (216-200)*100/48 = 33%          │
└────────────────────────────────────────────────┘

┌────────────────────────────────────────────────┐
│ Bytes 26-28: Quality (nibbles)                 │
│ Byte 26: 0xD8 → F3=8, FC5=13 (clamped to 4)  │
│ Byte 27: 0x34 → AF3=4, F7=3                   │
│ Byte 28: 0x21 → T7=1, P7=2                    │
│ → F3: Good(4), FC5: Good(4), AF3: Good(4)     │
│ → F7: Fair(3), T7: Very poor(1), P7: Poor(2)  │
└────────────────────────────────────────────────┘

┌────────────────────────────────────────────────┐
│ Byte 29: 0x68 = 104                            │
│ → Gyro X raw = 104                             │
│ → Gyro X signed = 104 - 104 = 0 (stable!)     │
└────────────────────────────────────────────────┘

┌────────────────────────────────────────────────┐
│ Byte 30: 0x6A = 106                            │
│ → Gyro Y raw = 106                             │
│ → Gyro Y signed = 106 - 104 = +2 (stable)     │
└────────────────────────────────────────────────┘
```

### Parsed Output:
```python
{
    'counter': 42,
    'battery': 33,
    'gyro_x': 0,      # Headset stable in X
    'gyro_y': 2,      # Headset stable in Y
    'sensors': {
        'F3': 4231,
        'FC5': 4567,
        # ... 12 more sensors
    },
    'quality': {
        'F3': 4,      # 🟢 Good
        'FC5': 4,     # 🟢 Good
        'AF3': 4,     # 🟢 Good
        'F7': 3,      # 🟡 Fair
        'T7': 1,      # 🔴 Very poor - needs adjustment!
        'P7': 2,      # 🟠 Poor - needs adjustment!
        # ... 8 more sensors
    }
}
```

## Signal Quality Visualization

```
Ideal Setup (all sensors good):
┌─────────────────────────────────────┐
│  Sensor Status                      │
├─────────────────────────────────────┤
│  F3:  🟢🟢🟢🟢 (4/4)                │
│  FC5: 🟢🟢🟢🟢 (4/4)                │
│  AF3: 🟢🟢🟢🟢 (4/4)                │
│  F7:  🟢🟢🟢🟢 (4/4)                │
│  ... all sensors good               │
│                                     │
│  ✓ Ready to record!                 │
└─────────────────────────────────────┘

Poor Setup (needs adjustment):
┌─────────────────────────────────────┐
│  Sensor Status                      │
├─────────────────────────────────────┤
│  F3:  🟢🟢🟢🟢 (4/4)                │
│  FC5: 🟡🟡🟡   (3/4)                │
│  AF3: 🟠🟠     (2/4) ⚠️              │
│  F7:  🔴       (1/4) ⚠️⚠️            │
│  T7:  ⚫       (0/4) ⚠️⚠️⚠️          │
│                                     │
│  ✗ Adjust headset before recording! │
│  → Moisten AF3, F7, T7 sensor pads  │
└─────────────────────────────────────┘
```

## Gyroscope Movement Detection

```
Head Movement Visualization:

  gyro_y < -10 (Forward tilt)
         ↑
         │
gyro_x < -10 ← [HEAD] → gyro_x > +10
(Left)          │         (Right)
         │
         ↓
  gyro_y > +10 (Backward tilt)

Stable Zone: |gyro_x| < 3 AND |gyro_y| < 3

Example Readings:
┌──────────────────────────────────────┐
│ gyro_x =  0, gyro_y =  1  → Stable   │
│ gyro_x = +5, gyro_y = -3  → Slight   │
│ gyro_x = +15, gyro_y = +2 → Moving!  │
│ gyro_x = -20, gyro_y = +8 → Moving!  │
└──────────────────────────────────────┘
```

## Quick Reference Card

```
╔══════════════════════════════════════════════╗
║     EMOTIV EPOC GEN 1 - QUICK REFERENCE      ║
╠══════════════════════════════════════════════╣
║ Counter    │ Byte 0         │ 0-255          ║
║ Sensors    │ Bytes 1-25     │ 14×14 bits     ║
║ Battery    │ Byte 26        │ 0-100%         ║
║ Quality    │ Bytes 26-28    │ 0-4 per sensor ║
║ Gyro X     │ Byte 29        │ -104 to +151   ║
║ Gyro Y     │ Byte 30        │ -104 to +151   ║
╠══════════════════════════════════════════════╣
║ AES Key: 31003554381037423100354838003750    ║
║ Packet Size: 32 bytes                        ║
║ Sample Rate: ~128 Hz                         ║
╚══════════════════════════════════════════════╝
```

## Troubleshooting Guide

### Problem: All quality values are 0
```
Possible causes:
1. Headset not powered on
2. Sensors not touching scalp
3. Sensor pads are dry
4. Wrong firmware version (quality encoding differs)

Solutions:
→ Ensure headset is on and connected
→ Position headset properly on head
→ Moisten sensor pads with saline solution
→ Check if raw bytes 26-28 change when adjusting sensors
```

### Problem: Gyro stuck at 104 or similar value
```
Possible cause:
→ Rust code not rebuilt with new gyro conversion

Solution:
→ cd bci/emotiv/lib
→ maturin develop --release
→ Verify gyro_x/gyro_y are now signed (can be negative)
```

### Problem: Battery shows 0% but headset is on
```
Possible causes:
1. Battery encoding differs in your firmware
2. Need to adjust conversion thresholds

Solution:
→ Check raw value at byte 26 (should be 200-248)
→ If outside this range, adjust conversion formula
→ Example: Some versions use 180-220 range
```

## See Also

- `PACKET_STRUCTURE.md` - Detailed technical specification
- `EMOTIV_IMPROVEMENTS.md` - Implementation details
- `CHANGES_SUMMARY.md` - Quick overview of changes

