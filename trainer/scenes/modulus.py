"""ModulusScene - ML Pipeline execution scene following MVC architecture."""

import pygame as pg
import threading
from trainer.scenes.base_scene import BaseScene
from trainer.scenes.modulus_model import ModulusModel
from trainer.scenes.modulus_view import ModulusView
from trainer.scenes.modulus_controller import ModulusController


class ModulusScene(BaseScene):
    """
    Scene for running Modulus ML Pipeline and browsing trained models.

    Follows MVC architecture:
    - Model: ModulusModel - holds state and data
    - View: ModulusView - handles rendering
    - Controller: ModulusController - handles input and updates model
    
    Features:
    - Run preprocessing experiments (binary, multiclass, or both)
    - Browse and load trained models from experiments or models/ folder
    - Copy selected model to model.pkl for use in driving scene
    """

    def __init__(self, screen, clock):
        super().__init__(screen, clock)
        self.model = ModulusModel()
        self.view = ModulusView(screen)
        self.controller = ModulusController(self.model)
        self.pipeline_thread = None
        # Register cleanup on exit
        import atexit
        atexit.register(self._cleanup)

    def run(self):
        """Main scene loop."""
        self.running = True

        while self.running:
            # Handle events (Controller)
            for e in pg.event.get():
                if e.type == pg.QUIT:
                    # Kill any running processes before quitting
                    self._cleanup()
                    self.running = False
                elif e.type == pg.KEYDOWN:
                    action = self.controller.handle_keydown(e.key)
                    if action == "quit":
                        # If pipeline complete or in browse mode, just go back to menu
                        if self.model.pipeline_complete or self.model.view_mode == "browse":
                            if self.model.view_mode == "browse":
                                # If in browse mode, reset error
                                self.model.model_load_error = None
                            self.model.pipeline_complete = False
                            self.model.error_message = None
                            self.model.view_mode = "experiments"
                        else:
                            # Kill any running processes before quitting
                            self._cleanup()
                            self.running = False
                    elif action == "run":
                        self._start_pipeline()
                    elif action == "load_model":
                        self._load_model()
                    elif action == "copy_model":
                        self._copy_model()

            # Update model state
            self._update_model()

            # Render (View)
            self.view.render(self.model)

            pg.display.flip()
            self.clock.tick(60)
        
        # Cleanup when exiting the scene
        self._cleanup()

    def _load_model(self):
        """Load the selected model."""
        if self.model.load_selected_model():
            # Success message (shown via model.loaded_model_info)
            pass
        # Error message will be shown via model.model_load_error
    
    def _copy_model(self):
        """Copy selected model to model.pkl for driving and load it."""
        if self.model.copy_model_to_main():
            # Also load the model into the store for immediate use
            self._load_model()

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
                # Get experiment configuration
                quick_mode = self.model.quick_mode
                hyperparameter_tuning = self.model.hyperparameter_tuning
                
                # Update step messages based on mode and configuration
                mode_label = {
                    "binary": "Binary Classification",
                    "multiclass": "Multiclass Classification",
                    "both": "Both Modes",
                }.get(mode, mode)

                # Phase 1: Baseline
                self.model.update_step(
                    f"Starting {mode_label} experiments...",
                    phase="baseline",
                    progress=0
                )
                pg.time.wait(300)
                
                self.model.update_step(
                    "Loading and preparing data...",
                    phase="baseline",
                    progress=5
                )
                pg.time.wait(300)
                
                self.model.update_step(
                    "Phase 1: Running baseline experiments (all configurations)...",
                    phase="baseline",
                    progress=10
                )
                pg.time.wait(200)

                # Execute actual experiments
                success, result, results_path = self.controller.execute_experiments(
                    mode, 
                    quick_mode, 
                    hyperparameter_tuning, 
                    self.model.n_jobs,
                    top_k=self.model.top_k,
                    cv_folds=self.model.cv_folds,
                )

                if success:
                    # Update progress to complete
                    self.model.update_step(
                        "Generating reports and visualizations...",
                        phase="complete",
                        progress=95
                    )
                    pg.time.wait(200)
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
        
        # Simulate progress updates while pipeline is running
        if self.model.pipeline_running and self.model.progress_percent < 90:
            # Slowly increment progress to give visual feedback
            import time
            current_time = time.time()
            if not hasattr(self, '_last_progress_update'):
                self._last_progress_update = current_time
            
            # Update progress every 2 seconds
            if current_time - self._last_progress_update > 2.0:
                self._last_progress_update = current_time
                # Slow down as we get closer to completion
                increment = max(1, (90 - self.model.progress_percent) // 20)
                new_progress = min(90, self.model.progress_percent + increment)
                
                # Update step messages based on progress
                if new_progress < 30:
                    step_msg = "Phase 1: Running baseline experiments..."
                    phase = "baseline"
                elif new_progress < 60:
                    step_msg = "Phase 1: Evaluating baseline configurations..."
                    phase = "baseline"
                elif new_progress < 75 and self.model.hyperparameter_tuning:
                    step_msg = f"Phase 2: Tuning top {self.model.top_k} configurations..."
                    phase = "tuning"
                elif new_progress < 85:
                    step_msg = "Analyzing results..."
                    phase = "tuning" if self.model.hyperparameter_tuning else "baseline"
                else:
                    step_msg = "Generating reports..."
                    phase = "complete"
                
                self.model.update_step(step_msg, phase=phase, progress=new_progress)
    
    def _cleanup(self):
        """Clean up resources, including killing any active subprocesses."""
        if self.controller:
            self.controller.kill_all_processes()
