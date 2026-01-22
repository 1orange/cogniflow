"""MenuScene - Main menu following MVC architecture."""

import pygame as pg
from config import SAMPLE_RATE, N_CHANNELS
from trainer.scenes.base_scene import BaseScene
from trainer.scenes.menu_model import MenuModel
from trainer.scenes.menu_view import MenuView
from trainer.scenes.menu_controller import MenuController
from trainer.utils.source_manager import source_manager
from trainer.scenes.calibration import CalibrationScene
from trainer.scenes.driving import DrivingScene
from trainer.scenes.record import RecordScene
from trainer.scenes.modulus import ModulusScene
from trainer.scenes.live import LiveScene
from trainer.scenes.settings import SettingsScene
from trainer.model_store import model_store


class MenuScene(BaseScene):
    """
    Scene for main menu navigation.

    Follows MVC architecture:
    - Model: MenuModel - holds state and data
    - View: MenuView - handles rendering
    - Controller: MenuController - handles input and updates model
    """

    def __init__(self, screen, clock):
        super().__init__(screen, clock)
        self.model = MenuModel()
        self.view = MenuView(screen)
        self.controller = MenuController(self.model)

        # Auto-select a device if none selected
        if not source_manager.has_source():
            source_manager.auto_select()
        
        self.model.set_source_info(SAMPLE_RATE, N_CHANNELS)

    def _get_source(self):
        """Get current data source from manager."""
        return source_manager.get_source()

    def run(self):
        """Main menu loop."""
        self.running = True
        W, H = self.screen.get_size()

        while self.running:
            # Handle events (Controller)
            for e in pg.event.get():
                if e.type == pg.QUIT:
                    self.running = False
                elif e.type == pg.KEYDOWN:
                    action = self.controller.handle_keydown(e.key)

                    if action == "quit":
                        self.running = False
                    elif action == "settings":
                        settings = SettingsScene(self.screen, self.clock)
                        settings.run()
                    elif action == "calibrate":
                        calibration = CalibrationScene(
                            self.screen, self.clock, self._get_source()
                        )
                        calibration.run()
                    elif action == "record":
                        record = RecordScene(self.screen, self.clock, self._get_source())
                        record.run()
                    elif action == "drive_bci":
                        # Check if model is loaded in model store first
                        if model_store.has_model:
                            driving = DrivingScene(
                                self.screen,
                                self.clock,
                                self._get_source(),
                                model=model_store.model,
                                control_mode="bci",
                            )
                            driving.run()
                        else:
                            # Try to load from default path
                            if model_store.load_default_model():
                                driving = DrivingScene(
                                    self.screen,
                                    self.clock,
                                    self._get_source(),
                                    model=model_store.model,
                                    control_mode="bci",
                                )
                                driving.run()
                            else:
                                self.screen.fill(self.view.colors["dark_bg"])
                                self.view.draw_text(
                                    "No model found.",
                                    W // 2,
                                    H // 2 - 30,
                                    32,
                                    self.view.colors["red"],
                                    True,
                                )
                                self.view.draw_text(
                                    "Use [M] ML Pipeline to train and load a model.",
                                    W // 2,
                                    H // 2 + 10,
                                    24,
                                    self.view.colors["yellow"],
                                    True,
                                )
                                pg.display.flip()
                                pg.time.wait(2000)
                    elif action == "drive_bci_no_model":
                        self.screen.fill(self.view.colors["dark_bg"])
                        self.view.draw_text(
                            "No model found. Use ML Pipeline first.",
                            W // 2,
                            H // 2,
                            32,
                            self.view.colors["red"],
                            True,
                        )
                        pg.display.flip()
                        pg.time.wait(1200)
                    elif action == "drive_arrow":
                        driving = DrivingScene(
                            self.screen,
                            self.clock,
                            self._get_source(),
                            model=None,  # No model needed for arrow mode
                            control_mode="arrow",
                        )
                        driving.run()
                    elif action == "modulus":
                        modulus = ModulusScene(self.screen, self.clock)
                        modulus.run()
                        # After returning from modulus, update model status
                        # (model might have been loaded in browse mode)
                    elif action == "live":
                        live = LiveScene(self.screen, self.clock, self._get_source())
                        live.run()

            # Update model status based on model store
            self.model.update_model_status(model_store)
            
            # Update device info
            self.model.set_device_info(source_manager.get_device_name(), source_manager.is_dummy())
            
            # Render (View)
            self.view.render(self.model)

            pg.display.flip()
            self.clock.tick(120)
