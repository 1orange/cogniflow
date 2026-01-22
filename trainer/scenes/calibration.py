"""CalibrationScene - BCI calibration following MVC architecture."""

import time
import pygame as pg
from concurrent.futures import ThreadPoolExecutor
from trainer.scenes.base_scene import BaseScene
from trainer.scenes.calibration_model import CalibrationModel
from trainer.scenes.calibration_view import CalibrationView
from trainer.scenes.calibration_controller import CalibrationController


class CalibrationScene(BaseScene):
    """
    Scene for BCI calibration process.

    Follows MVC architecture:
    - Model: CalibrationModel - holds state and data
    - View: CalibrationView - handles rendering
    - Controller: CalibrationController - handles input and coordinates calibration
    """

    def __init__(self, screen, clock, source):
        super().__init__(screen, clock)
        self.model = CalibrationModel()
        self.view = CalibrationView(screen)
        self.controller = CalibrationController(self.model, source)
        self.executor = ThreadPoolExecutor(max_workers=1)

    def run(self):
        """Run the calibration process."""
        self.running = True
        self.controller.start()

        try:
            # Calibration loop
            while self.running:
                dt = self.clock.tick(60) / 1000.0

                # Update phase timing
                continue_calibration, elapsed, remaining, total = (
                    self.controller.update_phase_timing()
                )
                if not continue_calibration:
                    break  # All trials complete

                # Update source label
                self.controller.update_source_label()

                # Read samples
                n_need = int(dt * self.model.fs)
                if n_need > 0:
                    samples = self.source.read(n_need)
                    self.model.add_samples(samples)

                # Extract windows during task phase
                if self.model.phase == "task":
                    extracted = self.model.extract_windows()
                    for win in extracted:
                        self.model.windows[self.model.intended].append(win)

                # Handle events (Controller)
                for e in pg.event.get():
                    if e.type == pg.QUIT:
                        self.running = False
                    elif e.type == pg.KEYDOWN:
                        action = self.controller.handle_keydown(e.key)
                        if action == "quit":
                            self.running = False

                # Render (View)
                self.view.render_calibration(self.model, elapsed, remaining, total)
                pg.display.flip()

        finally:
            # Ensure source is always stopped
            self.controller.stop()

        # Training phase
        self._run_training()

        # Completion screen
        self._show_completion()

    def _run_training(self):
        """Run model training asynchronously."""

        def train_model_async():
            # Placeholder training - integrate your pipeline here
            return 0.85  # Placeholder balanced accuracy

        # Submit training task
        training_future = self.executor.submit(train_model_async)

        # Wait for training with progress indication
        while not training_future.done():
            self.view.render_training(self.model)
            pg.display.flip()
            time.sleep(0.1)

        # Get training result
        try:
            bal = training_future.result()
            self.model.set_training_result(bal)
        except Exception as e:
            self.model.set_training_error(str(e))

    def _show_completion(self):
        """Show completion screen and wait for ESC."""
        waiting = True
        try:
            while waiting:
                self.view.render_complete(self.model)
                pg.display.flip()

                for e in pg.event.get():
                    if e.type == pg.QUIT or (
                        e.type == pg.KEYDOWN and e.key == pg.K_ESCAPE
                    ):
                        waiting = False
                self.clock.tick(30)
        finally:
            # Cleanup
            self.executor.shutdown(wait=True)
