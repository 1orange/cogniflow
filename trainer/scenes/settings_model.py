"""Model for SettingsScene - holds device selection state."""

from typing import Optional, List
from bci.devices import DeviceInfo, DeviceType


class SettingsModel:
    """Model for device settings and selection."""

    def __init__(self):
        self.available_devices: List[DeviceInfo] = []
        self.selected_index: int = 0
        self.current_device: Optional[DeviceInfo] = None
        self.status_message: str = "Press [R] to refresh devices"
        self.error_message: Optional[str] = None
        
    def set_devices(self, devices: List[DeviceInfo]):
        """Update available devices list."""
        self.available_devices = devices
        # Reset selection if out of bounds
        if self.selected_index >= len(devices):
            self.selected_index = max(0, len(devices) - 1)
            
    def set_current_device(self, device: Optional[DeviceInfo]):
        """Set currently active device."""
        self.current_device = device
        # Update selected index to match current device
        if device:
            for i, d in enumerate(self.available_devices):
                if d.name == device.name:
                    self.selected_index = i
                    break
    
    def move_selection(self, delta: int):
        """Move selection up or down."""
        if not self.available_devices:
            return
        self.selected_index = (self.selected_index + delta) % len(self.available_devices)
        
    def get_selected_device(self) -> Optional[DeviceInfo]:
        """Get currently highlighted device."""
        if 0 <= self.selected_index < len(self.available_devices):
            return self.available_devices[self.selected_index]
        return None
    
    def set_status(self, message: str):
        """Set status message."""
        self.status_message = message
        self.error_message = None
        
    def set_error(self, message: str):
        """Set error message."""
        self.error_message = message
        
    def is_device_active(self, device: DeviceInfo) -> bool:
        """Check if device is the currently active one."""
        if not self.current_device:
            return False
        return device.name == self.current_device.name

