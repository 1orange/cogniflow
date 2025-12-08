"""Controller for ModulusScene - handles input events and updates model."""

import pygame as pg
import sys
from pathlib import Path


class ModulusController:
    """Controller for ModulusScene - maps input to model updates."""

    def __init__(self, model):
        self.model = model

    def handle_keydown(self, key):
        """
        Handle keydown events and update model accordingly.

        Args:
            key: pygame key constant

        Returns:
            str: Action taken ('quit', 'run', 'none')
        """
        if key == pg.K_ESCAPE:
            return "quit"
        elif key == pg.K_UP:
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
        elif key == pg.K_RETURN or key == pg.K_KP_ENTER:
            if not self.model.pipeline_running:
                return "run"
        return "none"

    def execute_experiments(self, mode, quick_mode, hyperparameter_tuning):
        """
        Execute preprocessing experiments.

        Args:
            mode: Experiment mode ('binary', 'multiclass', or 'both')
            quick_mode: Whether to run quick mode (fewer experiments)
            hyperparameter_tuning: Whether to enable hyperparameter tuning

        Returns:
            tuple: (success: bool, summary: str or error: str, results_path: str or None)
        """
        import io
        import subprocess
        from contextlib import redirect_stdout, redirect_stderr
        from datetime import datetime

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

                # Add hyperparameter tuning flag
                if hyperparameter_tuning:
                    mode_cmd.append("--hyperparameter-tuning")

                # Capture stdout/stderr
                stdout_capture = io.StringIO()
                stderr_capture = io.StringIO()

                print(f"Running {current_mode} experiments...")

                # Run the script
                with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                    result = subprocess.run(
                        mode_cmd,
                        cwd=str(modulus_dir),
                        capture_output=True,
                        text=True,
                        timeout=3600 * 12,  # 12 hours timeout
                    )

                if result.returncode != 0:
                    error_msg = result.stderr or result.stdout or "Unknown error"
                    return (
                        False,
                        f"Error running {current_mode} experiments: {error_msg}",
                        None,
                    )

                output = stdout_capture.getvalue() or result.stdout
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
                            "experiments",
                            "top configuration",
                        ]
                    ):
                        if line.strip() and len(line.strip()) < 100:
                            summary_lines.append(line.strip())

            summary = (
                "\n".join(summary_lines[:20])
                if summary_lines
                else "Experiments completed successfully."
            )

            # Combine results paths
            if len(all_results_paths) == 1:
                results_path = all_results_paths[0]
            else:
                results_path = f"{len(all_results_paths)} result directories"

            return True, summary, results_path

        except subprocess.TimeoutExpired:
            return False, "Experiments timed out after 12 hours", None
        except Exception as e:
            error_msg = str(e)
            # Truncate very long error messages
            if len(error_msg) > 500:
                error_msg = error_msg[:500] + "..."
            return False, error_msg, None
