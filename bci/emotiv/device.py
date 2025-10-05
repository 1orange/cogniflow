"""
Device enumeration and selection using pyhidapi
"""

from typing import Any, List, Optional

import pyhidapi

from .constants import DEFAULT_VID, DEFAULT_PID


class HIDDeviceWrapper:
    """Simple wrapper to ensure close is always available."""

    def __init__(self, device: Any):
        """
        Initialize wrapper with a HID device handle.
        
        Args:
            device: Opaque HID device pointer from pyhidapi
        """
        self._device = device

    @property
    def device(self) -> Any:
        """Return the wrapped HID device handle."""
        return self._device

    def close(self) -> None:
        """Close the HID device."""
        try:
            pyhidapi.hid_close(self._device)
        except Exception:
            pass


def init() -> None:
    pyhidapi.hid_init()


def exit() -> None:
    pyhidapi.hid_exit()


def enumerate_devices(
    vid: int = DEFAULT_VID, pid: int = DEFAULT_PID
) -> List[pyhidapi.hid_device_info]:
    return list(pyhidapi.hid_enumerate(vid, pid) or [])


def open_best_interface(
    vid: int = DEFAULT_VID, pid: int = DEFAULT_PID
) -> Optional[HIDDeviceWrapper]:
    """
    Open the likely data interface first. On EPOC, interface 1 tends to be data.
    Fallback to any other matching interface if needed.
    """
    devs = enumerate_devices(vid, pid)
    if not devs:
        return None

    # Prefer interface 1, then 0, then the rest
    prioritized = sorted(
        devs, key=lambda d: (d.interface_number != 1, d.interface_number)
    )
    for info in prioritized:
        try:
            dev = pyhidapi.hid_open_path(info.path)
            if dev:
                return HIDDeviceWrapper(dev)
        except Exception:
            continue
    return None
