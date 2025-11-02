## emotiv-rs (embedded under bci/emotiv/lib)

Rust-based USB reader for Emotiv headsets with Python bindings via PyO3.

### Quick Install (Development Mode - Recommended)

This installs the extension directly into your virtualenv:

```bash
cd bci/emotiv/lib
./install_dev.sh
```

Or manually:

```bash
cd bci/emotiv/lib
maturin develop --release
```

Python import remains `emotiv_rs`.

### Build Wheel (For Distribution)

Build the wheel and place it in the `wheels/` directory:

```bash
cd bci/emotiv/lib
./build_wheel.sh
```

Or manually:

```bash
cd bci/emotiv/lib
maturin build --release --out wheels
```

Then install with:

```bash
pip install bci/emotiv/lib/wheels/emotiv_rs-*.whl
```

### Usage

```python
from emotiv_rs import EmotivReader, DEFAULT_VID, DEFAULT_PID, DEFAULT_PACKET_SIZE

# With custom VID/PID and AES key
reader = EmotivReader(
    vid=0x1234,
    pid=0xED02,
    packet_size=32,
    aes_key_hex="31003554381037423100354838003750"
)
reader.start()

try:
    while True:
        parsed = reader.poll_parsed()
        if parsed is not None:
            print(parsed)
finally:
    reader.stop()
```
