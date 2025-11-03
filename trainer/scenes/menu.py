import pygame as pg
import os
from config import *
from trainer.scenes.base_scene import BaseScene
from trainer.utils.source_manager import SourceManager
from trainer.scenes.calibration import CalibrationScene
from trainer.scenes.driving import DrivingScene
from trainer.scenes.record import RecordScene


class MenuScene(BaseScene):
    """Handles the main menu system with calibration, drive mode selection, and control mode selection."""

    def __init__(self, screen, clock):
        super().__init__(screen, clock)

        # Initialize source manager
        self.source_manager = SourceManager()
        self.source = self.source_manager.get_source()
        self.model_path = "models/model.pkl"

    def run(self):
        """Main menu loop."""
        self.running = True
        W, H = self.screen.get_size()

        while self.running:
            self.screen.fill(self.colors["dark_bg"])

            # Title
            self.draw_text(
                "BCI Car Trainer", W // 2, 90, 48, self.colors["white"], True
            )

            # Menu options
            self.draw_text(
                "[R] Record Data", W // 2, 240, 36, self.colors["green"], True
            )
            self.draw_text("[C] Calibrate", W // 2, 200, 36, self.colors["green"], True)
            self.draw_text(
                "[A] Drive (Arrow Keys)", W // 2, 320, 36, self.colors["green"], True
            )
            self.draw_text(
                "[D] Drive (BCI)", W // 2, 280, 36, self.colors["green"], True
            )
            self.draw_text("[ESC] Quit", W // 2, 380, 28, self.colors["yellow"], True)

            # System info
            self.draw_text(
                "Source: EMOTIV EPOC",
                W // 2,
                450,
                24,
                self.colors["white"],
                True,
            )
            self.draw_text(
                f"Sample rate: {SAMPLE_RATE} Hz | Channels: {N_CHANNELS}",
                W // 2,
                480,
                22,
                self.colors["white"],
                True,
            )

            # Model status
            model_status = (
                "Available"
                if os.path.exists(self.model_path)
                else "Not found - Calibrate first"
            )
            model_color = (
                self.colors["green"]
                if os.path.exists(self.model_path)
                else self.colors["red"]
            )
            self.draw_text(f"Model: {model_status}", W // 2, 510, 22, model_color, True)

            # Handle events
            for e in pg.event.get():
                if e.type == pg.QUIT:
                    self.running = False
                elif e.type == pg.KEYDOWN:
                    match e.key:
                        case pg.K_ESCAPE:
                            self.running = False

                        case pg.K_c:
                            # Run calibration scene
                            calibration = CalibrationScene(
                                self.screen, self.clock, self.source
                            )
                            calibration.run()

                        case pg.K_r:
                            # Run record scene
                            record = RecordScene(self.screen, self.clock, self.source)
                            record.run()

                        case pg.K_d:
                            # Run BCI driving scene
                            if os.path.exists(self.model_path):
                                driving = DrivingScene(
                                    self.screen,
                                    self.clock,
                                    self.source,
                                    self.model_path,
                                    "bci",
                                )
                                driving.run()
                            else:
                                self.screen.fill(self.colors["dark_bg"])
                                self.draw_text(
                                    "No model found. Calibrate first.",
                                    W // 2,
                                    H // 2,
                                    32,
                                    self.colors["red"],
                                    True,
                                )
                                pg.display.flip()
                                pg.time.wait(1200)

                        case pg.K_a:
                            # Run arrow key driving scene
                            driving = DrivingScene(
                                self.screen,
                                self.clock,
                                self.source,
                                self.model_path,
                                "arrow",
                            )
                            driving.run()

                        case _:
                            # Optional: handle unassigned keys
                            pass


            pg.display.flip()
            self.clock.tick(120)
