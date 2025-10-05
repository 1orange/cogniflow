"""
EEGer library: Emotiv EPOC data access

Public API:
- EEGReader: High-level reader to acquire, decrypt, and parse EEG packets
- constants: Default VID/PID, AES key
- sensors: Sensor maps and parsing helpers
"""

from .reader import EEGReader
from . import constants
from . import sensors

__all__ = [
    "EEGReader",
    "constants",
    "sensors",
]
