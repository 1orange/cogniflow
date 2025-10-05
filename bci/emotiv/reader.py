"""
High-level EEGReader API
"""

import time
from dataclasses import dataclass
from typing import Dict, Iterator, Optional, Any, List

import pyhidapi

from .constants import PACKET_SIZE_BYTES, DEFAULT_VID, DEFAULT_PID
from .crypto import decrypt_packet
from .sensors import parse_sensor_data
from . import device as device_mod


@dataclass
class ParsedPacket:
    counter: int
    gyro_x: int
    gyro_y: int
    sensors: Dict[str, int]
    timestamp: float


class EEGReader:
    """
    Provides convenient methods to stream raw packets, decrypted packets, and parsed data.
    Handles device initialization, open, and cleanup.
    """

    def __init__(self, vid: int = DEFAULT_VID, pid: int = DEFAULT_PID):
        self.vid = vid
        self.pid = pid
        self._dev: Optional[Any] = None  # Opaque HID device pointer
        self._initialized: bool = False

    def __enter__(self) -> "EEGReader":
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def open(self) -> None:
        if not self._initialized:
            device_mod.init()
            self._initialized = True
        wrapper = device_mod.open_best_interface(self.vid, self.pid)
        if not wrapper:
            raise RuntimeError(
                "No Emotiv EPOC device found or could not open any interface"
            )
        self._dev = wrapper.device
        pyhidapi.hid_set_nonblocking(self._dev, 1)

    def close(self) -> None:
        if self._dev is not None:
            try:
                pyhidapi.hid_close(self._dev)
            except Exception:
                pass
            self._dev = None
        if self._initialized:
            device_mod.exit()
            self._initialized = False

    def read_raw_packets(self) -> Iterator[bytes]:
        if self._dev is None:
            raise RuntimeError("Device not open")
        while True:
            data = pyhidapi.hid_read(self._dev, PACKET_SIZE_BYTES)
            if data:
                yield data
            else:
                print("Missing packet, waiting for next one...")
                time.sleep(0.005)

    def read_decrypted_packets(self) -> Iterator[bytes]:
        for raw in self.read_raw_packets():
            decrypted = decrypt_packet(raw)
            if decrypted is not None:
                yield decrypted

    def read_parsed(self) -> Iterator[ParsedPacket]:
        for dec in self.read_decrypted_packets():
            parsed = parse_sensor_data(dec)
            if parsed is None:
                continue
            yield ParsedPacket(
                counter=parsed["counter"],
                gyro_x=parsed["gyro_x"],
                gyro_y=parsed["gyro_y"],
                sensors=parsed["sensors"],
                timestamp=time.time(),
            )

    def record(self, duration_seconds: float) -> List[Dict[str, Any]]:
        """Collect parsed packets for a fixed duration and return them as dicts."""
        end_time = time.time() + max(0.0, duration_seconds)
        results: List[Dict[str, Any]] = []
        for pkt in self.read_parsed():
            results.append(
                {
                    "counter": pkt.counter,
                    "gyro_x": pkt.gyro_x,
                    "gyro_y": pkt.gyro_y,
                    "sensors": pkt.sensors,
                    "timestamp": pkt.timestamp,
                }
            )
            if time.time() >= end_time:
                break
        return results
