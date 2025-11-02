"""
Constants for Emotiv EPOC communication and decryption

This module now proxies constants from the Rust extension `emotiv_rs` to ensure
single source of truth across Python and Rust implementations.
"""

from emotiv_rs import DEFAULT_VID, DEFAULT_PID, DEFAULT_PACKET_SIZE

# Backwards-compatible aliases
PACKET_SIZE_BYTES: int = DEFAULT_PACKET_SIZE
