"""
Source manager for EEG data providers.

Manages the selection and initialization of different EEG data sources
including real devices and simulated dummy sources.
"""

from typing import Optional, Union
from config import SAMPLE_RATE, N_CHANNELS
from bci.devices import DeviceInfo, DeviceType, enumerate_all_devices, get_dummy_device


# Type alias for data providers
DataProviderType = Union["DataProvider", "DummyDataProvider"]


class SourceManager:
    """
    Manages EEG data source selection and initialization.
    
    Supports:
    - Emotiv EPOC devices
    - Dummy/simulated data for testing
    """

    _instance = None  # Singleton instance
    
    def __new__(cls):
        """Singleton pattern to ensure one source manager."""
        if cls._instance is None:
            cls._instance = super(SourceManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self.source: Optional[DataProviderType] = None
        self.current_device: Optional[DeviceInfo] = None
        self.available_devices: list[DeviceInfo] = []
        self._initialized = True
        
        # Scan for devices on init
        self.refresh_devices()
        
    def refresh_devices(self) -> list[DeviceInfo]:
        """
        Refresh the list of available devices.
        
        Returns:
            List of available DeviceInfo
        """
        self.available_devices = enumerate_all_devices()
        return self.available_devices
    
    def select_device(self, device: DeviceInfo) -> bool:
        """
        Select a device to use as the data source.
        
        Args:
            device: DeviceInfo to select
            
        Returns:
            True if device was successfully selected and initialized
        """
        # Stop current source if running
        if self.source:
            try:
                self.source.stop()
            except Exception:
                pass
            self.source = None
            
        try:
            if device.device_type == DeviceType.EMOTIV_EPOC:
                from bci.data_provider import DataProvider
                self.source = DataProvider(
                    fs=SAMPLE_RATE,
                    n_channels=N_CHANNELS,
                    vid=device.vid,
                    pid=device.pid,
                )
            elif device.device_type == DeviceType.DUMMY:
                from bci.dummy_provider import DummyDataProvider
                self.source = DummyDataProvider(
                    fs=SAMPLE_RATE,
                    n_channels=N_CHANNELS,
                )
            else:
                print(f"Unknown device type: {device.device_type}")
                return False
                
            self.current_device = device
            print(f"Selected device: {device.name}")
            return True
            
        except Exception as e:
            print(f"Error selecting device: {e}")
            self.source = None
            self.current_device = None
            return False
    
    def select_device_by_index(self, index: int) -> bool:
        """
        Select a device by its index in the available devices list.
        
        Args:
            index: Index of device to select
            
        Returns:
            True if successful
        """
        if 0 <= index < len(self.available_devices):
            return self.select_device(self.available_devices[index])
        return False
    
    def select_dummy(self) -> bool:
        """Select the dummy device for testing."""
        dummy = get_dummy_device()
        return self.select_device(dummy)
    
    def auto_select(self) -> bool:
        """
        Automatically select the best available device.
        
        Prefers real devices over dummy.
        
        Returns:
            True if a device was selected
        """
        self.refresh_devices()
        
        # Try real devices first
        for device in self.available_devices:
            if device.device_type != DeviceType.DUMMY and device.available:
                if self.select_device(device):
                    return True
                    
        # Fall back to dummy
        return self.select_dummy()

    def get_source(self) -> Optional[DataProviderType]:
        """Get the current data source."""
        return self.source
    
    def has_source(self) -> bool:
        """Check if a source is selected."""
        return self.source is not None
    
    def get_device_name(self) -> str:
        """Get name of current device or 'None'."""
        if self.current_device:
            return self.current_device.name
        return "None"
    
    def is_dummy(self) -> bool:
        """Check if current source is the dummy device."""
        return (
            self.current_device is not None 
            and self.current_device.device_type == DeviceType.DUMMY
        )


# Global instance
source_manager = SourceManager()
