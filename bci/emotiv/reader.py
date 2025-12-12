"""
High-level EEGReader API backed by the Rust `emotiv_rs` extension.
"""

import time
from dataclasses import dataclass
from typing import Dict, Iterator, Any, List

from emotiv_rs import EmotivReader as _RsReader
from .constants import DEFAULT_VID, DEFAULT_PID, PACKET_SIZE_BYTES


@dataclass
class ParsedPacket:
    counter: int
    gyro_x: int
    gyro_y: int
    battery: int  # Battery percentage (0-100)
    sensors: Dict[str, int]
    quality: Dict[str, int]  # Signal quality for each sensor (0-4)
    timestamp: float


class EEGReader:
    """
    Streams raw, decrypted, and parsed packets via the Rust backend.
    """

    def __init__(
        self,
        vid: int = DEFAULT_VID,
        pid: int = DEFAULT_PID,
        aes_key_hex: str | None = None,
    ):
        self.vid = vid
        self.pid = pid
        self._rs = _RsReader(vid, pid, PACKET_SIZE_BYTES, aes_key_hex)
        self._opened = False

    def __enter__(self) -> "EEGReader":
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def open(self) -> None:
        if not self._opened:
            self._rs.start()
            self._opened = True

    def close(self) -> None:
        if self._opened:
            self._rs.stop()
            self._opened = False

    def read_raw_packets(self) -> Iterator[bytes]:
        if not self._opened:
            raise RuntimeError("Device not open")
        while True:
            pkt = self._rs.poll_raw()
            if pkt is not None:
                yield pkt
            else:
                time.sleep(0.005)

    def read_decrypted_packets(self) -> Iterator[bytes]:
        if not self._opened:
            raise RuntimeError("Device not open")
        while True:
            pkt = self._rs.poll_decrypted()
            if pkt is not None:
                yield pkt
            else:
                time.sleep(0.005)

    def read_parsed(self) -> Iterator[ParsedPacket]:
        if not self._opened:
            raise RuntimeError("Device not open")
        while True:
            parsed = self._rs.poll_parsed()
            if parsed is None:
                time.sleep(0.005)
                continue
            yield ParsedPacket(
                counter=int(parsed["counter"]),
                gyro_x=int(parsed["gyro_x"]),
                gyro_y=int(parsed["gyro_y"]),
                battery=int(parsed["battery"]),
                sensors=dict(parsed["sensors"]),
                quality=dict(parsed["quality"]),
                timestamp=time.time(),
            )

    def record(self, duration_seconds: float) -> List[Dict[str, Any]]:
        end_time = time.time() + max(0.0, duration_seconds)
        results: List[Dict[str, Any]] = []
        for pkt in self.read_parsed():
            results.append(
                {
                    "counter": pkt.counter,
                    "gyro_x": pkt.gyro_x,
                    "gyro_y": pkt.gyro_y,
                    "battery": pkt.battery,
                    "sensors": pkt.sensors,
                    "quality": pkt.quality,
                    "timestamp": pkt.timestamp,
                }
            )
            if time.time() >= end_time:
                break
        return results
