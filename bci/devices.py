"""
Device enumeration and management for BCI data sources.

Provides a unified interface for discovering and selecting EEG devices,
including support for dummy/simulated devices for testing.
"""

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class DeviceType(Enum):
    """Supported device types."""
    EMOTIV_EPOC = "emotiv_epoc"
    DUMMY = "dummy"


@dataclass
class DeviceInfo:
    """Information about a detected or configured device."""
    device_type: DeviceType
    name: str
    description: str
    vid: Optional[int] = None
    pid: Optional[int] = None
    path: Optional[str] = None
    serial: Optional[str] = None
    available: bool = True
    
    def __str__(self) -> str:
        status = "✓" if self.available else "✗"
        return f"{status} {self.name}"
    
    @property
    def display_name(self) -> str:
        """Get display name for UI."""
        if self.device_type == DeviceType.DUMMY:
            return f"🔧 {self.name}"
        return f"🧠 {self.name}"


def enumerate_emotiv_devices() -> List[DeviceInfo]:
    """
    Enumerate connected Emotiv devices using hidapi.
    
    Returns:
        List of DeviceInfo for each detected Emotiv device.
    """
    devices = []
    
    try:
        import hid
        from bci.emotiv.constants import DEFAULT_VID, DEFAULT_PID
        
        # Enumerate HID devices
        all_devices = hid.enumerate(DEFAULT_VID, DEFAULT_PID)
        
        # Group by serial number (multiple interfaces per device)
        seen_serials = set()
        for dev in all_devices:
            serial = dev.get('serial_number', '')
            if serial and serial in seen_serials:
                continue
            if serial:
                seen_serials.add(serial)
            
            info = DeviceInfo(
                device_type=DeviceType.EMOTIV_EPOC,
                name=f"Emotiv EPOC ({serial[:8]}...)" if serial else "Emotiv EPOC",
                description=f"VID:{dev.get('vendor_id', 0):04X} PID:{dev.get('product_id', 0):04X}",
                vid=dev.get('vendor_id'),
                pid=dev.get('product_id'),
                path=dev.get('path', b'').decode('utf-8', errors='ignore') if isinstance(dev.get('path'), bytes) else dev.get('path'),
                serial=serial,
                available=True,
            )
            devices.append(info)
            
    except ImportError:
        # hidapi not available, try emotiv_rs
        try:
            from emotiv_rs import DEFAULT_VID, DEFAULT_PID
            # Can't enumerate without hidapi, but we can add a placeholder
            devices.append(DeviceInfo(
                device_type=DeviceType.EMOTIV_EPOC,
                name="Emotiv EPOC (auto-detect)",
                description="Will auto-detect on connection",
                vid=DEFAULT_VID,
                pid=DEFAULT_PID,
                available=True,
            ))
        except ImportError:
            pass
    except Exception as e:
        print(f"Error enumerating Emotiv devices: {e}")
    
    return devices


def get_dummy_device() -> DeviceInfo:
    """Get the dummy/simulated device info."""
    return DeviceInfo(
        device_type=DeviceType.DUMMY,
        name="Dummy Device (Simulated)",
        description="Generates synthetic EEG-like data for testing",
        available=True,
    )


def enumerate_all_devices() -> List[DeviceInfo]:
    """
    Enumerate all available devices including dummy.
    
    Returns:
        List of all available DeviceInfo, with dummy device last.
    """
    devices = []
    
    # Real devices first
    devices.extend(enumerate_emotiv_devices())
    
    # Always add dummy device for testing
    devices.append(get_dummy_device())
    
    return devices

