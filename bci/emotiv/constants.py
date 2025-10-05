"""
Constants for Emotiv EPOC communication and decryption
"""

# Known AES key from reverse engineering (hex string without spaces)
# Key: 31003554381037423100354838003750
AES_KEY_HEX: str = "31003554381037423100354838003750"

# Pre-decoded AES key bytes
AES_KEY: bytes = bytes.fromhex(AES_KEY_HEX)

# Default Vendor ID and Product ID for Emotiv EPOC Developer Headset
# To verify on your system, run: lsusb | grep -i emotiv
DEFAULT_VID: int = 0x1234
DEFAULT_PID: int = 0xED02

# Default HID packet size for EPOC (bytes)
PACKET_SIZE_BYTES: int = 32
