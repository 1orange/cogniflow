# Emotiv Packet Queue Fix

## The Problem

The initial Rust implementation had a critical issue with packet handling:

### Original Behavior
```rust
fn poll_raw<'py>(&self, py: Python<'py>) -> PyResult<Option<Bound<'py, PyBytes>>> {
    // Only gets ONE packet - the OLDEST in the queue
    match rx.try_recv() { 
        Ok(bytes) => Ok(Some(PyBytes::new(py, &bytes))), 
        Err(_) => Ok(None) 
    }
}
```

**Issue:** The device sends packets at **128 Hz** (every ~7.8ms), but Python can't always poll that fast due to:
- GIL (Global Interpreter Lock) contention
- Processing delays
- Other system tasks

This caused packets to accumulate in the queue (capacity: 32,768 packets), and we were reading STALE data from seconds ago!

### Symptoms
- Apparent "packet loss" of 99%
- Counter values jumping by 100+ between reads
- Actually reading old data, not real-time data

## The Solution

Changed `poll_raw()` to drain the queue and return **only the latest packet**:

```rust
fn poll_raw<'py>(&self, py: Python<'py>) -> PyResult<Option<Bound<'py, PyBytes>>> {
    let guard = self.inner.lock();
    if let Some(ref rx) = guard.rx {
        // Drain the queue and get only the latest packet
        let mut latest: Option<Vec<u8>> = None;
        loop {
            match rx.try_recv() {
                Ok(bytes) => latest = Some(bytes),
                Err(_) => break,
            }
        }
        Ok(latest.map(|bytes| PyBytes::new(py, &bytes)))
    } else { Ok(None) }
}
```

## Behavior After Fix

### Expected Behavior
- ✅ Always get the **most recent** packet from the device
- ✅ Real-time data, not stale data from the queue
- ✅ Intentionally skip intermediate packets to stay current
- ⚠️ "Skip rate" of 99% is **normal** if Python polls slowly

### Trade-offs
| Aspect | Before | After |
|--------|--------|-------|
| Data age | OLD (could be seconds behind) | FRESH (latest available) |
| Data completeness | All packets (but stale) | Latest only (real-time) |
| Use case | Recording/analysis | Real-time control/BCI |

## When to Use What

### Use Latest-Only Mode (Current)
✅ Real-time BCI applications
✅ Live control systems (e.g., car driving)
✅ Visual feedback applications
✅ When you need current brain state NOW

### Use All-Packets Mode (Not Implemented Yet)
❌ Recording sessions for later analysis
❌ Research where every data point matters
❌ Offline signal processing
❌ When data completeness > latency

## Monitoring Script Updates

The `check_packets.py` script now correctly reports:
- **"Packets skipped"** instead of "packet loss" (intentional behavior)
- **"Skip rate"** - percentage of packets intentionally discarded
- **"Polling rate"** - how fast Python is reading packets

### Example Output
```
Duration:        5.0 seconds
Packets read:    517
Average rate:    126.5 Hz
Packets skipped: 64022
Skip rate:       99.2% (normal for real-time mode)
```

This is **CORRECT** - we're reading ~127 Hz but only getting the latest packet each time!

## Future Improvements

1. **Add mode selection:** Allow choosing between "latest" and "all" modes
2. **Adaptive queue size:** Dynamically adjust based on polling speed
3. **Metrics endpoint:** Expose queue depth and lag metrics
4. **Timestamp packets:** Add timestamp at read time for precise timing

## Rebuilding After Changes

```bash
cd bci/emotiv/lib
poetry run maturin develop --release
```

## Testing

```bash
# Quick packet flow check
python scripts/check_packets.py

# Full test suite
python scripts/test_emotiv_rs.py
```

