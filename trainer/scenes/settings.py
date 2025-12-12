"""SettingsScene - Device selection and configuration."""

import pygame as pg

from trainer.scenes.base_scene import BaseScene
from trainer.scenes.settings_model import SettingsModel
from trainer.scenes.settings_view import SettingsView
from trainer.scenes.settings_controller import SettingsController
from trainer.utils.source_manager import source_manager


class SettingsScene(BaseScene):
    """
    Scene for selecting and configuring EEG data sources.
    
    Allows users to:
    - View available devices (Emotiv, Dummy)
    - Select which device to use
    - Refresh device list
    """

    def __init__(self, screen, clock):
        super().__init__(screen, clock)
        self.model = SettingsModel()
        self.view = SettingsView(screen)
        self.controller = SettingsController(self.model)
        
        # Load current state from source manager
        self._sync_from_manager()

    def _sync_from_manager(self):
        """Sync model state from source manager."""
        self.model.set_devices(source_manager.available_devices)
        self.model.set_current_device(source_manager.current_device)
        
    def _refresh_devices(self):
        """Refresh the device list."""
        self.model.set_status("Scanning for devices...")
        self.view.render(self.model)
        pg.display.flip()
        
        devices = source_manager.refresh_devices()
        self.model.set_devices(devices)
        self.model.set_current_device(source_manager.current_device)
        
        if devices:
            self.model.set_status(f"Found {len(devices)} device(s)")
        else:
            self.model.set_status("No devices found")
            
    def _select_device(self):
        """Select the currently highlighted device."""
        device = self.model.get_selected_device()
        if not device:
            self.model.set_error("No device selected")
            return
            
        self.model.set_status(f"Connecting to {device.name}...")
        self.view.render(self.model)
        pg.display.flip()
        
        success = source_manager.select_device(device)
        
        if success:
            self.model.set_current_device(device)
            self.model.set_status(f"Connected to {device.name}")
        else:
            self.model.set_error(f"Failed to connect to {device.name}")

    def run(self):
        """Main scene loop."""
        self.running = True
        
        while self.running:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.running = False
                elif event.type == pg.KEYDOWN:
                    action = self.controller.handle_keydown(event.key)
                    
                    if action == "quit":
                        self.running = False
                    elif action == "refresh":
                        self._refresh_devices()
                    elif action == "select":
                        self._select_device()
            
            self.view.render(self.model)
            pg.display.flip()
            self.clock.tick(60)

