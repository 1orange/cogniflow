"""
AES decryption helpers for Emotiv EPOC.

This module now delegates decryption to the Rust extension `emotiv_rs` for speed
and to keep the implementation in one place.
"""

from emotiv_rs import decrypt_packet as _rs_decrypt, decrypt_packet_with_key as _rs_decrypt_with_key
from .constants import PACKET_SIZE_BYTES


def decrypt_packet(encrypted_packet: bytes, aes_key_hex: str | None = None) -> bytes | None:
    """Decrypt a 32-byte packet using Rust implementation (PyO3 binding).

    If aes_key_hex is provided (32-hex chars), it's used; otherwise default key is used.
    """
    if len(encrypted_packet) != PACKET_SIZE_BYTES:
        return None
    if aes_key_hex:
        return _rs_decrypt_with_key(encrypted_packet, aes_key_hex)
    return _rs_decrypt(encrypted_packet)
