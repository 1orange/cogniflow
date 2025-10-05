"""
Sensor mappings and parsing helpers for Emotiv EPOC packets
"""

from typing import Dict, List, Tuple, Any


# Sensor names and their positions in the packet (for reference/metadata)
SENSORS: Dict[str, Tuple[int, int]] = {
    "AF3": (3, 4),  # Fp1
    "F7": (5, 6),  # F7
    "F3": (7, 8),  # F3
    "FC5": (9, 10),  # FC5
    "T7": (11, 12),  # T7
    "P7": (13, 14),  # P7
    "O1": (15, 16),  # O1
    "O2": (17, 18),  # O2
    "P8": (19, 20),  # P8
    "T8": (21, 22),  # T8
    "FC6": (23, 24),  # FC6
    "F4": (25, 26),  # F4
    "F8": (27, 28),  # F8
    "AF4": (29, 30),  # Fp2
}


# Bit positions for extracting 14-bit sensor levels from a 32-byte packet
SENSOR_BITS: Dict[str, List[Tuple[int, int]]] = {
    "F3": [
        (0, 6),
        (0, 7),
        (1, 0),
        (1, 1),
        (1, 2),
        (1, 3),
        (1, 4),
        (1, 5),
        (1, 6),
        (1, 7),
        (2, 0),
        (2, 1),
        (2, 2),
        (2, 3),
    ],
    "FC5": [
        (2, 4),
        (2, 5),
        (2, 6),
        (2, 7),
        (3, 0),
        (3, 1),
        (3, 2),
        (3, 3),
        (3, 4),
        (3, 5),
        (3, 6),
        (3, 7),
        (4, 0),
        (4, 1),
    ],
    "AF3": [
        (4, 2),
        (4, 3),
        (4, 4),
        (4, 5),
        (4, 6),
        (4, 7),
        (5, 0),
        (5, 1),
        (5, 2),
        (5, 3),
        (5, 4),
        (5, 5),
        (5, 6),
        (5, 7),
    ],
    "F7": [
        (6, 0),
        (6, 1),
        (6, 2),
        (6, 3),
        (6, 4),
        (6, 5),
        (6, 6),
        (6, 7),
        (7, 0),
        (7, 1),
        (7, 2),
        (7, 3),
        (7, 4),
        (7, 5),
    ],
    "T7": [
        (7, 6),
        (7, 7),
        (8, 0),
        (8, 1),
        (8, 2),
        (8, 3),
        (8, 4),
        (8, 5),
        (8, 6),
        (8, 7),
        (9, 0),
        (9, 1),
        (9, 2),
        (9, 3),
    ],
    "P7": [
        (9, 4),
        (9, 5),
        (9, 6),
        (9, 7),
        (10, 0),
        (10, 1),
        (10, 2),
        (10, 3),
        (10, 4),
        (10, 5),
        (10, 6),
        (10, 7),
        (11, 0),
        (11, 1),
    ],
    "O1": [
        (11, 2),
        (11, 3),
        (11, 4),
        (11, 5),
        (11, 6),
        (11, 7),
        (12, 0),
        (12, 1),
        (12, 2),
        (12, 3),
        (12, 4),
        (12, 5),
        (12, 6),
        (12, 7),
    ],
    "O2": [
        (13, 0),
        (13, 1),
        (13, 2),
        (13, 3),
        (13, 4),
        (13, 5),
        (13, 6),
        (13, 7),
        (14, 0),
        (14, 1),
        (14, 2),
        (14, 3),
        (14, 4),
        (14, 5),
    ],
    "P8": [
        (14, 6),
        (14, 7),
        (15, 0),
        (15, 1),
        (15, 2),
        (15, 3),
        (15, 4),
        (15, 5),
        (15, 6),
        (15, 7),
        (16, 0),
        (16, 1),
        (16, 2),
        (16, 3),
    ],
    "T8": [
        (16, 4),
        (16, 5),
        (16, 6),
        (16, 7),
        (17, 0),
        (17, 1),
        (17, 2),
        (17, 3),
        (17, 4),
        (17, 5),
        (17, 6),
        (17, 7),
        (18, 0),
        (18, 1),
    ],
    "FC6": [
        (18, 2),
        (18, 3),
        (18, 4),
        (18, 5),
        (18, 6),
        (18, 7),
        (19, 0),
        (19, 1),
        (19, 2),
        (19, 3),
        (19, 4),
        (19, 5),
        (19, 6),
        (19, 7),
    ],
    "F4": [
        (20, 0),
        (20, 1),
        (20, 2),
        (20, 3),
        (20, 4),
        (20, 5),
        (20, 6),
        (20, 7),
        (21, 0),
        (21, 1),
        (21, 2),
        (21, 3),
        (21, 4),
        (21, 5),
    ],
    "F8": [
        (21, 6),
        (21, 7),
        (22, 0),
        (22, 1),
        (22, 2),
        (22, 3),
        (22, 4),
        (22, 5),
        (22, 6),
        (22, 7),
        (23, 0),
        (23, 1),
        (23, 2),
        (23, 3),
    ],
    "AF4": [
        (23, 4),
        (23, 5),
        (23, 6),
        (23, 7),
        (24, 0),
        (24, 1),
        (24, 2),
        (24, 3),
        (24, 4),
        (24, 5),
        (24, 6),
        (24, 7),
        (25, 0),
        (25, 1),
    ],
}


def get_level(packet: bytes, sensor: str) -> int:
    """Extract the 14-bit EEG level for a given sensor from a decrypted packet."""
    bits = SENSOR_BITS[sensor]
    level = 0
    for i, (byte_idx, bit_idx) in enumerate(bits):
        level |= ((packet[byte_idx] >> bit_idx) & 1) << i
    return level


def parse_sensor_data(decrypted_packet: bytes) -> Dict[str, Any] | None:
    """
    Parse EEG and gyro data from a decrypted 32-byte packet.

    Returns a dictionary with keys: counter, gyro_x, gyro_y, sensors.
    """
    if len(decrypted_packet) != 32:
        return None

    counter = decrypted_packet[0]
    gyro_x = decrypted_packet[29]
    gyro_y = decrypted_packet[30]

    sensor_data: Dict[str, int] = {}
    for sensor in SENSOR_BITS.keys():
        sensor_data[sensor] = get_level(decrypted_packet, sensor)

    return {
        "counter": counter,
        "gyro_x": gyro_x,
        "gyro_y": gyro_y,
        "sensors": sensor_data,
    }
