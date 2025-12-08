"""Model for ModulusScene - holds state and data."""


class ModulusModel:
    """Model for ModulusScene - stores state and data without rendering logic."""

    def __init__(self):
        # Experiment mode selection
        self.experiment_modes = ["binary", "multiclass", "both"]
        self.selected_mode_index = 0

        # Hyperparameter tuning options
        self.hyperparameter_tuning = False
        self.quick_mode = False

        # Pipeline state
        self.pipeline_running = False
        self.pipeline_complete = False
        self.current_step = ""
        self.error_message = None
        self.results_summary = None
        self.results_path = None

    def get_selected_mode(self):
        """Get the currently selected experiment mode."""
        if 0 <= self.selected_mode_index < len(self.experiment_modes):
            return self.experiment_modes[self.selected_mode_index]
        return "binary"

    def select_next_mode(self):
        """Move to next experiment mode."""
        if self.experiment_modes:
            self.selected_mode_index = (self.selected_mode_index + 1) % len(
                self.experiment_modes
            )

    def select_previous_mode(self):
        """Move to previous experiment mode."""
        if self.experiment_modes:
            self.selected_mode_index = (self.selected_mode_index - 1) % len(
                self.experiment_modes
            )

    def toggle_hyperparameter_tuning(self):
        """Toggle hyperparameter tuning option."""
        self.hyperparameter_tuning = not self.hyperparameter_tuning

    def toggle_quick_mode(self):
        """Toggle quick mode option."""
        self.quick_mode = not self.quick_mode

    def start_pipeline(self):
        """Mark pipeline as starting."""
        self.pipeline_running = True
        self.pipeline_complete = False
        self.error_message = None
        self.results_summary = None
        self.results_path = None

    def update_step(self, step_name):
        """Update current pipeline step."""
        self.current_step = step_name

    def complete_pipeline(self, results_summary=None, results_path=None):
        """Mark pipeline as complete."""
        self.pipeline_running = False
        self.pipeline_complete = True
        self.results_summary = results_summary
        self.results_path = results_path
        self.current_step = ""

    def set_error(self, error_message):
        """Set error message."""
        self.pipeline_running = False
        self.pipeline_complete = False
        self.error_message = error_message
        self.current_step = ""
        self.results_path = None
