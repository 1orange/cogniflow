"""Controller for ModulusScene - handles input events and updates model."""

import pygame as pg
import sys
from pathlib import Path


class ModulusController:
    """Controller for ModulusScene - maps input to model updates."""

    def __init__(self, model):
        self.model = model
        self.active_processes = []  # Track active subprocesses for cleanup

    def handle_keydown(self, key):
        """
        Handle keydown events and update model accordingly.

        Args:
            key: pygame key constant

        Returns:
            str: Action taken ('quit', 'run', 'load_model', 'copy_model', 'none')
        """
        if key == pg.K_ESCAPE:
            return "quit"
        
        # B key toggles between browse and experiments mode
        if key == pg.K_b:
            self.model.toggle_view_mode()
            return "none"
        
        # Handle keys based on current view mode
        if self.model.view_mode == "browse":
            return self._handle_browse_keys(key)
        else:
            return self._handle_experiments_keys(key)
    
    def _handle_browse_keys(self, key):
        """Handle keys in browse mode."""
        if key == pg.K_UP:
            self.model.select_previous_model()
            return "none"
        elif key == pg.K_DOWN:
            self.model.select_next_model()
            return "none"
        elif key == pg.K_RETURN or key == pg.K_KP_ENTER:
            # Load selected model
            return "load_model"
        elif key == pg.K_c:
            # Copy model to model.pkl
            return "copy_model"
        elif key == pg.K_r:
            # Refresh model list
            self.model.scan_available_models()
            return "none"
        elif key == pg.K_PAGEUP:
            # Page up
            for _ in range(self.model.models_per_page):
                self.model.select_previous_model()
            return "none"
        elif key == pg.K_PAGEDOWN:
            # Page down
            for _ in range(self.model.models_per_page):
                self.model.select_next_model()
            return "none"
        elif key == pg.K_HOME:
            # Go to first model
            self.model.selected_model_index = 0
            self.model.browse_scroll_offset = 0
            return "none"
        elif key == pg.K_END:
            # Go to last model
            if self.model.available_models:
                self.model.selected_model_index = len(self.model.available_models) - 1
                self.model._update_scroll()
            return "none"
        return "none"
    
    def _handle_experiments_keys(self, key):
        """Handle keys in experiments mode."""
        if key == pg.K_UP:
            self.model.select_previous_mode()
            return "none"
        elif key == pg.K_DOWN:
            self.model.select_next_mode()
            return "none"
        elif key == pg.K_q:
            self.model.toggle_quick_mode()
            return "none"
        elif key == pg.K_h:
            self.model.toggle_hyperparameter_tuning()
            return "none"
        elif key == pg.K_PLUS or key == pg.K_KP_PLUS or key == pg.K_EQUALS:
            # Increase CPU count (+ or = key)
            self.model.increase_n_jobs()
            return "none"
        elif key == pg.K_MINUS or key == pg.K_KP_MINUS:
            # Decrease CPU count (- key)
            self.model.decrease_n_jobs()
            return "none"
        # Top-K controls (only when tuning is enabled)
        elif key == pg.K_t:
            # Decrease top-k
            if self.model.hyperparameter_tuning:
                self.model.decrease_top_k()
            return "none"
        elif key == pg.K_y:
            # Increase top-k
            if self.model.hyperparameter_tuning:
                self.model.increase_top_k()
            return "none"
        # CV folds controls (only when tuning is enabled)
        elif key == pg.K_f:
            # Decrease CV folds
            if self.model.hyperparameter_tuning:
                self.model.decrease_cv_folds()
            return "none"
        elif key == pg.K_g:
            # Increase CV folds
            if self.model.hyperparameter_tuning:
                self.model.increase_cv_folds()
            return "none"
        elif key == pg.K_RETURN or key == pg.K_KP_ENTER:
            if not self.model.pipeline_running:
                return "run"
        return "none"

    def execute_experiments(self, mode, quick_mode, hyperparameter_tuning, n_jobs=None, 
                           top_k=15, cv_folds=5):
        """
        Execute preprocessing experiments.

        Args:
            mode: Experiment mode ('binary', 'multiclass', or 'both')
            quick_mode: Whether to run quick mode (fewer experiments)
            hyperparameter_tuning: Whether to enable hyperparameter tuning
            n_jobs: Number of parallel jobs (None = use all CPUs)
            top_k: Number of top configurations to tune (new optimized workflow)
            cv_folds: Number of cross-validation folds for GridSearchCV

        Returns:
            tuple: (success: bool, summary: str or error: str, results_path: str or None)
        """
        import subprocess
        from datetime import datetime
        import os
        import signal

        # Get project root
        project_root = Path(__file__).parent.parent.parent
        modulus_dir = project_root / "modulus"
        results_dir = project_root / "results"
        results_dir.mkdir(exist_ok=True)

        # Add modulus directory to path
        if str(modulus_dir) not in sys.path:
            sys.path.insert(0, str(modulus_dir))

        try:
            # Prepare command arguments
            script_path = modulus_dir / "run_preprocessing_experiments.py"

            # Determine output directory based on mode
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if mode == "both":
                output_dirs = []
                for m in ["binary", "multiclass"]:
                    output_dir = results_dir / f"experiments_{m}_{timestamp}"
                    output_dirs.append(str(output_dir))
            else:
                output_dir = results_dir / f"experiments_{mode}_{timestamp}"
                output_dirs = [str(output_dir)]

            # Build command
            cmd = ["python3", str(script_path)]

            # Add mode argument(s)
            if mode == "both":
                # Run both modes sequentially
                modes_to_run = ["binary", "multiclass"]
            else:
                modes_to_run = [mode]

            all_output = []
            all_results_paths = []

            for current_mode in modes_to_run:
                mode_cmd = cmd + ["--mode", current_mode]

                # Add quick mode flag
                if quick_mode:
                    mode_cmd.append("--quick")

                # Set output directory for this mode
                if mode == "both":
                    mode_output = (
                        results_dir / f"experiments_{current_mode}_{timestamp}"
                    )
                else:
                    mode_output = output_dir
                mode_cmd.extend(["--output", str(mode_output)])

                # Add hyperparameter tuning flag and related options
                if hyperparameter_tuning:
                    mode_cmd.append("--hyperparameter-tuning")
                    mode_cmd.extend(["--top-k", str(top_k)])
                    mode_cmd.extend(["--cv-folds", str(cv_folds)])
                
                # Add n_jobs argument for parallelization
                if n_jobs is not None:
                    mode_cmd.extend(["--n-jobs", str(n_jobs)])

                print(f"Running {current_mode} experiments...")
                print(f"Command: {' '.join(mode_cmd)}")

                # Run the script using Popen to track the process
                process = subprocess.Popen(
                    mode_cmd,
                    cwd=str(modulus_dir),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    preexec_fn=os.setsid,  # Create new process group so we can kill children
                )
                
                # Track the process for cleanup
                self.active_processes.append(process)
                
                try:
                    # Wait for process to complete
                    stdout, stderr = process.communicate()
                    returncode = process.returncode
                finally:
                    # Remove from tracking once done
                    if process in self.active_processes:
                        self.active_processes.remove(process)

                if returncode != 0:
                    error_msg = stderr or stdout or "Unknown error"
                    return (
                        False,
                        f"Error running {current_mode} experiments: {error_msg}",
                        None,
                    )

                output = stdout
                all_output.append(output)
                all_results_paths.append(str(mode_output))

            # Extract summary from output
            summary_lines = []
            for output in all_output:
                for line in output.split("\n"):
                    if any(
                        keyword in line.lower()
                        for keyword in [
                            "complete",
                            "results saved",
                            "best",
                            "accuracy",
                            "f1",
                            "experiments",
                            "top configuration",
                            "test set",
                            "baseline",
                            "tuning",
                        ]
                    ):
                        if line.strip() and len(line.strip()) < 100:
                            summary_lines.append(line.strip())

            summary = (
                "\n".join(summary_lines[:25])
                if summary_lines
                else "Experiments completed successfully."
            )

            # Combine results paths
            if len(all_results_paths) == 1:
                results_path = all_results_paths[0]
            else:
                results_path = f"{len(all_results_paths)} result directories"

            return True, summary, results_path

        except KeyboardInterrupt:
            # User interrupted - kill all processes
            self.kill_all_processes()
            return False, "Experiments interrupted by user", None
        except Exception as e:
            error_msg = str(e)
            # Truncate very long error messages
            if len(error_msg) > 500:
                error_msg = error_msg[:500] + "..."
            # Ensure processes are killed on error
            self.kill_all_processes()
            return False, error_msg, None
    
    def kill_all_processes(self):
        """Kill all active subprocesses."""
        import subprocess
        import os
        import signal
        
        for process in self.active_processes[:]:  # Copy list to avoid modification during iteration
            try:
                if process.poll() is None:  # Process is still running
                    # Try to terminate the entire process group (kills pool workers too)
                    try:
                        pgid = os.getpgid(process.pid)
                        os.killpg(pgid, signal.SIGTERM)
                    except Exception:
                        # Fallback to terminate the main process
                        process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        try:
                            pgid = os.getpgid(process.pid)
                            os.killpg(pgid, signal.SIGKILL)
                        except Exception:
                            process.kill()
                        process.wait()
            except Exception as e:
                # Process may have already terminated
                print(f"Error killing process: {e}")
            finally:
                # Remove from tracking
                if process in self.active_processes:
                    self.active_processes.remove(process)
