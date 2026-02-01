"""RecordScene - Data recording wizard following MVC architecture."""

import time
import pygame as pg
from concurrent.futures import ThreadPoolExecutor
from trainer.scenes.base_scene import BaseScene
from trainer.scenes.record_model import RecordModel
from trainer.scenes.record_view import RecordView
from trainer.scenes.record_controller import RecordController


class RecordScene(BaseScene):
    """
    Scene for BCI data recording wizard.

    Follows MVC architecture:
    - Model: RecordModel - holds state and data
    - View: RecordView - handles rendering
    - Controller: RecordController - handles input and coordinates recording
    """

    def __init__(self, screen, clock, source):
        super().__init__(screen, clock)
        self.model = RecordModel()
        self.view = RecordView(screen)
        self.controller = RecordController(self.model, source)
        self.executor = ThreadPoolExecutor(max_workers=1)

    def run(self):
        """Run the data recording wizard."""
        # Step 1: Select directions
        if not self._run_wizard_step("select_directions"):
            return

        # Step 2: Select window duration
        if not self._run_wizard_step("select_window"):
            return

        # Step 3: Select trials count
        if not self._run_wizard_step("select_trials"):
            return

        # Step 4: Record data
        self._record_data()

        # Step 5: Save data
        self._save_data()

        # Step 6: Show completion
        self._show_completion()

    def _run_wizard_step(self, step):
        """Run a wizard step and return True if should continue."""
        self.model.wizard_step = step
        self.running = True

        while self.running:
            # Handle events (Controller)
            for e in pg.event.get():
                if e.type == pg.QUIT:
                    return False
                elif e.type == pg.KEYDOWN:
                    action = self.controller.handle_keydown(e.key, step)
                    if action == "cancel":
                        return False
                    elif action == "continue":
                        return True

            # Render (View)
            if step == "select_directions":
                self.view.render_select_directions(self.model)
            elif step == "select_window":
                self.view.render_select_window(self.model)
            elif step == "select_trials":
                self.view.render_select_trials(self.model)

            pg.display.flip()
            self.clock.tick(60)

        return False

    def _record_data(self):
        """Perform the actual data recording."""
        self.model.wizard_step = "recording"
        self.controller.start_recording()
        self.running = True

        try:
            while self.running:
                dt = self.clock.tick(60) / 1000.0

                # Update phase timing
                continue_recording, elapsed, remaining, total = (
                    self.controller.update_phase_timing()
                )
                if not continue_recording:
                    break  # All trials complete

                # Update source label
                self.controller.update_source_label()

                # Read samples
                n_need = int(dt * self.model.fs)
                if n_need > 0:
                    samples = self.controller.source.read(n_need)
                    self.model.add_samples(samples)

                # Extract windows during task phase
                if self.model.phase == "task":
                    extracted = self.model.extract_windows()
                    for win in extracted:
                        self.model.recorded_data[self.model.intended].append(win)

                # Handle events (Controller)
                for e in pg.event.get():
                    if e.type == pg.QUIT:
                        self.running = False
                    elif e.type == pg.KEYDOWN:
                        action = self.controller.handle_keydown(e.key, "recording")
                        if action == "cancel":
                            self.running = False

                # Render (View)
                self.view.render_recording(self.model, elapsed, remaining, total)
                pg.display.flip()

        finally:
            self.controller.stop_recording()

    def _save_data(self):
        """Save recorded data asynchronously."""
        self.model.wizard_step = "saving"

        def save_async():
            return self.controller.save_data()

        saving_future = self.executor.submit(save_async)

        while not saving_future.done():
            self.view.render_saving(self.model)
            pg.display.flip()
            time.sleep(0.1)

        saving_future.result()
        self.model.saving_complete = True

    def _show_completion(self):
        """Show completion screen."""
        self.model.wizard_step = "complete"
        waiting = True

        try:
            while waiting:
                self.view.render_complete(self.model)
                pg.display.flip()

                for e in pg.event.get():
                    if e.type == pg.QUIT:
                        waiting = False
                    elif e.type == pg.KEYDOWN:
                        action = self.controller.handle_keydown(e.key, "complete")
                        if action == "quit":
                            waiting = False
                self.clock.tick(30)
        finally:
            self.executor.shutdown(wait=True)
