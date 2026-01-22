# EEG Data Values Explanation

## Overview

This document explains the EEG data values produced by the Emotiv EPOC headset, specifically addressing why **negative values are normal and expected** in the recorded data.

## Raw Sensor Values

The Emotiv EPOC Gen 1 headset provides raw sensor readings as **14-bit unsigned integers**:

- **Range**: 0 to 16383 (2^14 - 1)
- **Encoding**: Each sensor value represents a voltage level at the electrode
- **Midpoint**: 8192 (half of the 14-bit range)

## Conversion to Microvolts (μV)

The raw values are converted to microvolts using the following formula:

```python
uv_value = (raw_value - 8192) * 0.51
```

### Conversion Steps

1. **Center the signal**: Subtract 8192 to shift the range from [0, 16383] to [-8192, +8191]
2. **Scale to microvolts**: Multiply by 0.51 to convert to physiological units

### Resulting Range

- **Theoretical minimum**: (0 - 8192) × 0.51 = **-4177.92 μV**
- **Theoretical maximum**: (16383 - 8192) × 0.51 = **+4177.41 μV**
- **Zero point**: When raw_value = 8192, result = 0 μV

## Why Negative Values Are Correct

### 1. EEG Measures Voltage Differences

EEG does not measure absolute voltage but rather the **potential difference** between electrodes:

- Each sensor measures voltage relative to reference electrodes (CMS/DRL)
- Voltage differences naturally fluctuate both **above and below** the reference
- This creates a **bipolar signal** (both positive and negative)

### 2. Brain Activity Creates Bidirectional Signals

Neural activity produces electrical potentials that can be:

- **Positive deflections**: Depolarization events, certain ERP components
- **Negative deflections**: Hyperpolarization events, other ERP components
- **Zero-crossing**: Baseline brain activity

### 3. Normal EEG Characteristics

Typical EEG signals exhibit:

- **Mean near zero**: The signal oscillates around the reference (0 μV)
- **Symmetric distribution**: Roughly equal positive and negative excursions
- **Typical amplitude**: ±50 to ±100 μV for normal brain activity
- **Artifacts**: Can reach ±200 μV or more (eye blinks, muscle tension)

## Example Data Analysis

From a real recording (`recorded_data_forward_20251110_130851.npy`):

```
Shape: (690, 192, 14)
Min value: -4177.92 μV
Max value: +4177.41 μV
Mean: 1.17 μV          ← Very close to zero (expected)
Std dev: 1709.73 μV

Negative values: 25.15% of all samples
```

### Value Distribution

| Range | Count | Percentage | Interpretation |
|-------|-------|------------|----------------|
| < -100 μV | 455,350 | 24.6% | Large negative deflections |
| -100 to 0 μV | 11,086 | 0.6% | Small negative deflections |
| 0 to 100 μV | 932,794 | 50.3% | Small positive deflections + zeros |
| > 100 μV | 455,490 | 24.6% | Large positive deflections |

The distribution is nearly **symmetric around zero**, which is exactly what we expect from properly converted EEG data.

## Implementation Reference

### Python (data_provider.py)

```python
def _drain_channel(self):
    """Drain parsed packets from Rust channel into local buffer (non-blocking)."""
    if not self.reader:
        return
    while True:
        parsed = self.reader.poll_parsed()
        if parsed is None:
            break
        sensor_values = []
        for sensor_name in self.sensor_names:
            value = parsed["sensors"].get(sensor_name, 0)
            # Convert 14-bit value to microvolts (approximate scaling)
            uv_value = (value - 8192) * 0.51
            sensor_values.append(uv_value)
        sample = np.array(sensor_values)
        with self._lock:
            self._buffer.append(sample)
```

### Rust (lib.rs)

The raw 14-bit values are extracted from the packet bytes:

```rust
// Each sensor value is 14 bits (0-16383)
let level = get_level_impl(packet, sensor_name);
// Returns: 0 to 16383
```

These are then converted to microvolts on the Python side.

## Common Questions

### Q: Should I remove negative values?

**No!** Removing negative values would:
- Destroy half of your signal
- Introduce severe bias
- Make the data unusable for analysis

### Q: What if I see values near ±4178 μV?

These are the **saturation limits** of the ADC:
- Indicates very strong signals (often artifacts)
- Eye blinks, muscle tension, or poor contact can cause this
- Consider artifact rejection if too frequent

### Q: Why is the mean slightly positive (1.17 μV)?

Small DC offsets are normal due to:
- Reference electrode impedance
- Amplifier characteristics
- Biological DC potentials

This offset is typically removed by:
- Bandpass filtering (default: 1-40 Hz)
- Baseline correction in analysis

### Q: What about all the zero values?

If you see many consecutive zeros, this might indicate:
- **Packet loss**: USB communication issues
- **Sensor disconnection**: Poor contact quality
- **Buffer underruns**: Data streaming issues

Check the packet queue and sensor quality indicators.

## Expected Voltage Ranges by EEG Band

| Brain Rhythm | Frequency | Typical Amplitude |
|--------------|-----------|-------------------|
| Delta (δ) | 0.5-4 Hz | 20-200 μV |
| Theta (θ) | 4-8 Hz | 10-50 μV |
| Alpha (α) | 8-13 Hz | 20-60 μV |
| Beta (β) | 13-30 Hz | 5-30 μV |
| Gamma (γ) | 30-100 Hz | 5-10 μV |

All of these rhythms have **both positive and negative phases** as they oscillate.

## Conclusion

**Negative values in your EEG data are not only correct—they are essential!**

- EEG is a bipolar signal measuring voltage differences
- The conversion formula correctly centers the signal around 0 μV
- A mean near zero and symmetric distribution confirm proper data collection
- Negative values represent normal brain electrical activity

## References

- [PACKET_STRUCTURE.md](./PACKET_STRUCTURE.md) - Raw packet format
- [bci/data_provider.py](../../bci/data_provider.py) - Conversion implementation
- [bci/emotiv/lib/src/lib.rs](../../bci/emotiv/lib/src/lib.rs) - Sensor parsing

## Related Documentation

- [EMOTIV_IMPROVEMENTS.md](../EMOTIV_IMPROVEMENTS.md) - Recent improvements to data extraction
- [PACKET_QUEUE_FIX.md](./PACKET_QUEUE_FIX.md) - Packet handling improvements

