"""
AES decryption helpers for Emotiv EPOC
"""

from Crypto.Cipher import AES

from .constants import AES_KEY, PACKET_SIZE_BYTES


def decrypt_packet(encrypted_packet: bytes) -> bytes | None:
    """Decrypt a 32-byte packet using AES-ECB (two 16-byte blocks)."""
    if len(encrypted_packet) != PACKET_SIZE_BYTES:
        return None

    try:
        cipher = AES.new(AES_KEY, AES.MODE_ECB)
        decrypted = b""
        for i in range(0, PACKET_SIZE_BYTES, 16):
            block = encrypted_packet[i : i + 16]
            decrypted += cipher.decrypt(block)
        return decrypted
    except Exception:
        return None
