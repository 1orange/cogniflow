"""ModulusScene - ML Pipeline execution scene following MVC architecture."""

import pygame as pg
import threading
from trainer.scenes.base_scene import BaseScene
from trainer.scenes.modulus_model import ModulusModel
from trainer.scenes.modulus_view import ModulusView
from trainer.scenes.modulus_controller import ModulusController


class ModulusScene(BaseScene):
    """
    Scene for running Modulus ML Pipeline.

    Follows MVC architecture:
    - Model: ModulusModel - holds state and data
    - View: ModulusView - handles rendering
    - Controller: ModulusController - handles input and updates model
    """

    def __init__(self, screen, clock):
        super().__init__(screen, clock)
        self.model = ModulusModel()
        self.view = ModulusView(screen)
        self.controller = ModulusController(self.model)
        self.pipeline_thread = None

    def run(self):
        """Main scene loop."""
        self.running = True

        while self.running:
            # Handle events (Controller)
            for e in pg.event.get():
                if e.type == pg.QUIT:
                    self.running = False
                elif e.type == pg.KEYDOWN:
                    action = self.controller.handle_keydown(e.key)
                    if action == "quit":
                        # Wait for pipeline to finish if running
                        if self.pipeline_thread and self.pipeline_thread.is_alive():
                            # Can't easily cancel, just mark for exit
                            pass
                        self.running = False
                    elif action == "run":
                        self._start_pipeline()

            # Update model state
            self._update_model()

            # Render (View)
            self._render()

            pg.display.flip()
            self.clock.tick(60)

    def _start_pipeline(self):
        """Start experiment execution in a separate thread."""
        if self.model.pipeline_running:
            return

        mode = self.model.get_selected_mode()
        if not mode:
            return

        self.model.start_pipeline()

        def run_experiments():
            """Run experiments and update model."""
            try:
                # Update step messages based on mode
                mode_label = {
                    "binary": "Binary Classification",
                    "multiclass": "Multiclass Classification",
                    "both": "Both Modes",
                }.get(mode, mode)

                steps = [
                    f"Starting {mode_label} experiments...",
                    "Loading data...",
                    "Running preprocessing experiments...",
                    "Training models...",
                    "Evaluating configurations...",
                    "Analyzing results...",
                    "Generating reports...",
                ]

                step_idx = 0
                for step in steps:
                    if not self.running:
                        break
                    self.model.update_step(step)
                    pg.time.wait(500)  # Small delay for UI updates
                    step_idx += 1

                # Execute actual experiments
                success, result, results_path = self.controller.execute_experiments(
                    mode, self.model.quick_mode, self.model.hyperparameter_tuning
                )

                if success:
                    self.model.complete_pipeline(result, results_path)
                else:
                    self.model.set_error(result)

            except Exception as e:
                self.model.set_error(str(e))

        self.pipeline_thread = threading.Thread(target=run_experiments, daemon=True)
        self.pipeline_thread.start()

    def _update_model(self):
        """Update model state (called each frame)."""
        # Model updates happen through controller actions
        # This is where we could add time-based updates if needed
        pass

    def _render(self):
        """Render current state using view."""
        if self.model.error_message:
            self.view.render_error(self.model)
        elif self.model.pipeline_complete:
            self.view.render_complete(self.model)
        elif self.model.pipeline_running:
            self.view.render_running(self.model)
        else:
            self.view.render_menu(self.model)
