"""
Sensor parsing now delegates to Rust (`emotiv_rs`) for performance and parity.
"""

from typing import Dict, Any

from emotiv_rs import get_level as _rs_get_level, parse_sensor_data as _rs_parse


def get_level(packet: bytes, sensor: str) -> int:
    level = _rs_get_level(packet, sensor)
    if level is None:
        raise KeyError(sensor)
    return level


def parse_sensor_data(decrypted_packet: bytes) -> Dict[str, Any] | None:
    return _rs_parse(decrypted_packet)
