"""
Device handling now lives in the Rust extension `emotiv_rs`.

This module remains for API compatibility; most callers should use
`bci.emotiv.reader.EEGReader` which now delegates to Rust directly.
"""

from .constants import DEFAULT_VID, DEFAULT_PID


def init() -> None:  # kept for compatibility
    return None


def exit() -> None:  # kept for compatibility
    return None


def enumerate_devices(vid: int = DEFAULT_VID, pid: int = DEFAULT_PID):  # pragma: no cover
    """Enumeration is handled internally by the Rust reader; returns empty list."""
    return []


def open_best_interface(vid: int = DEFAULT_VID, pid: int = DEFAULT_PID):  # pragma: no cover
    """Device opening is handled internally by the Rust reader; returns None."""
    return None
