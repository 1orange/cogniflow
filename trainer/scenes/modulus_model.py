"""Model for ModulusScene - holds state and data."""

import multiprocessing
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List
import json


@dataclass
class ModelInfo:
    """Information about a trained model."""
    path: Path
    name: str
    source: str  # "experiments" or "models"
    experiment_name: Optional[str] = None
    model_type: Optional[str] = None
    preprocessing: Optional[str] = None
    split_ratio: Optional[str] = None
    accuracy: Optional[float] = None
    f1_score: Optional[float] = None
    timestamp: Optional[str] = None
    
    @classmethod
    def from_experiments_path(cls, path: Path) -> "ModelInfo":
        """Create ModelInfo from an experiments best_model.pkl path."""
        experiment_dir = path.parent
        experiment_name = experiment_dir.name
        
        # Try to load metrics from JSON file
        accuracy = None
        f1_score = None
        model_type = None
        preprocessing = None
        split_ratio = None
        
        # Find the latest JSON file
        json_files = list(experiment_dir.glob("all_experiments_*.json"))
        if json_files:
            try:
                with open(sorted(json_files)[-1], 'r') as f:
                    data = json.load(f)
                    # Find best result
                    best = None
                    best_f1 = -1
                    for result in data:
                        if result.get("status") == "success":
                            f1 = result.get("f1_score", 0)
                            if f1 > best_f1:
                                best_f1 = f1
                                best = result
                    if best:
                        accuracy = best.get("accuracy")
                        f1_score = best.get("f1_score")
                        model_type = best.get("model")
                        preprocessing = best.get("preprocessing")
                        split_ratio = best.get("split_ratio")
            except Exception:
                pass
        
        display_name = experiment_name
        if model_type:
            display_name = f"{experiment_name} ({model_type})"
        
        return cls(
            path=path,
            name=display_name,
            source="experiments",
            experiment_name=experiment_name,
            model_type=model_type,
            preprocessing=preprocessing,
            split_ratio=split_ratio,
            accuracy=accuracy,
            f1_score=f1_score,
        )
    
    @classmethod
    def from_models_path(cls, path: Path) -> "ModelInfo":
        """Create ModelInfo from a models/*.pkl path."""
        filename = path.stem
        parts = filename.split("_")
        
        # Parse filename: ModelType_Preprocessing_SplitRatio_Timestamp.pkl
        model_type = parts[0] if len(parts) > 0 else None
        
        # Find split ratio (format like 70_15_15 or 80_10_10)
        split_ratio = None
        preprocessing_parts = []
        timestamp_parts = []
        
        for i, part in enumerate(parts[1:], 1):
            if part in ["70", "80"] and i + 2 < len(parts):
                # Check if next parts form a split ratio
                try:
                    int(parts[i + 1])
                    int(parts[i + 2])
                    split_ratio = f"{part}/{parts[i + 1]}/{parts[i + 2]}"
                    timestamp_parts = parts[i + 3:]
                    break
                except (ValueError, IndexError):
                    pass
            preprocessing_parts.append(part)
        
        preprocessing = "_".join(preprocessing_parts) if preprocessing_parts else None
        timestamp = "_".join(timestamp_parts) if timestamp_parts else None
        
        display_name = filename
        if model_type and preprocessing:
            display_name = f"{model_type}: {preprocessing}"
            if split_ratio:
                display_name += f" ({split_ratio})"
        
        return cls(
            path=path,
            name=display_name,
            source="models",
            model_type=model_type,
            preprocessing=preprocessing,
            split_ratio=split_ratio,
            timestamp=timestamp,
        )


class ModulusModel:
    """Model for ModulusScene - stores state and data without rendering logic."""

    def __init__(self):
        # View mode: "experiments" or "browse"
        self.view_mode = "experiments"
        
        # Experiment mode selection
        self.experiment_modes = ["binary", "multiclass", "both"]
        self.selected_mode_index = 0

        # Hyperparameter tuning options
        self.hyperparameter_tuning = False
        self.quick_mode = False
        
        # CPU count for parallelization
        self.max_cpus = multiprocessing.cpu_count()
        self.n_jobs = self.max_cpus  # Default: use all CPUs
        
        # Top-K selection for hyperparameter tuning (new optimized workflow)
        self.top_k = 15  # Number of top configs to tune
        self.top_k_min = 5
        self.top_k_max = 30
        
        # Cross-validation folds for GridSearchCV
        self.cv_folds = 5
        self.cv_folds_min = 3
        self.cv_folds_max = 10

        # Pipeline state
        self.pipeline_running = False
        self.pipeline_complete = False
        self.current_step = ""
        self.current_phase = ""  # "baseline" or "tuning"
        self.progress_percent = 0  # 0-100
        self.error_message = None
        self.results_summary = None
        self.results_path = None
        
        # Model browser state
        self.available_models: List[ModelInfo] = []
        self.selected_model_index = 0
        self.loaded_model = None
        self.loaded_model_info: Optional[ModelInfo] = None
        self.model_load_error: Optional[str] = None
        self.browse_scroll_offset = 0  # For scrolling long lists
        self.models_per_page = 8  # How many models to show at once
        
        # Project paths
        self._project_root = Path(__file__).parent.parent.parent

    def toggle_view_mode(self):
        """Toggle between experiments and browse modes."""
        if self.view_mode == "experiments":
            self.view_mode = "browse"
            self.scan_available_models()
        else:
            self.view_mode = "experiments"
            self.model_load_error = None

    def scan_available_models(self):
        """Scan for available trained models."""
        self.available_models = []
        
        results_dir = self._project_root / "results"
        models_dir = self._project_root / "models"
        
        # Scan experiment results for best_model.pkl
        if results_dir.exists():
            for experiment_dir in sorted(results_dir.iterdir(), reverse=True):
                if experiment_dir.is_dir():
                    best_model = experiment_dir / "best_model.pkl"
                    if best_model.exists():
                        try:
                            info = ModelInfo.from_experiments_path(best_model)
                            self.available_models.append(info)
                        except Exception:
                            pass
        
        # Scan models directory for individual models
        if models_dir.exists():
            for model_file in sorted(models_dir.glob("*.pkl"), reverse=True):
                try:
                    info = ModelInfo.from_models_path(model_file)
                    self.available_models.append(info)
                except Exception:
                    pass
        
        # Reset selection
        self.selected_model_index = 0
        self.browse_scroll_offset = 0
        self.model_load_error = None

    def select_next_model(self):
        """Select next model in the list."""
        if self.available_models:
            self.selected_model_index = (self.selected_model_index + 1) % len(self.available_models)
            self._update_scroll()
    
    def select_previous_model(self):
        """Select previous model in the list."""
        if self.available_models:
            self.selected_model_index = (self.selected_model_index - 1) % len(self.available_models)
            self._update_scroll()
    
    def _update_scroll(self):
        """Update scroll offset to keep selection visible."""
        if self.selected_model_index < self.browse_scroll_offset:
            self.browse_scroll_offset = self.selected_model_index
        elif self.selected_model_index >= self.browse_scroll_offset + self.models_per_page:
            self.browse_scroll_offset = self.selected_model_index - self.models_per_page + 1
    
    def get_visible_models(self) -> List[ModelInfo]:
        """Get the currently visible models based on scroll offset."""
        start = self.browse_scroll_offset
        end = start + self.models_per_page
        return self.available_models[start:end]
    
    def get_selected_model_info(self) -> Optional[ModelInfo]:
        """Get the currently selected model info."""
        if 0 <= self.selected_model_index < len(self.available_models):
            return self.available_models[self.selected_model_index]
        return None
    
    def load_selected_model(self):
        """Load the currently selected model into the global model store."""
        from trainer.model_store import model_store
        
        info = self.get_selected_model_info()
        if not info:
            self.model_load_error = "No model selected"
            return False
        
        try:
            success = model_store.load_model(
                path=str(info.path),
                name=info.name,
                model_type=info.model_type,
                preprocessing=info.preprocessing,
                accuracy=info.accuracy,
                f1_score=info.f1_score,
            )
            
            if success:
                self.loaded_model = model_store.model
                self.loaded_model_info = info
                self.model_load_error = None
                return True
            else:
                self.model_load_error = "Failed to load model"
                self.loaded_model = None
                self.loaded_model_info = None
                return False
        except Exception as e:
            self.model_load_error = f"Failed to load model: {str(e)}"
            self.loaded_model = None
            self.loaded_model_info = None
            return False
    
    def copy_model_to_main(self):
        """Copy selected model to models/model.pkl for use in driving."""
        import shutil
        
        info = self.get_selected_model_info()
        if not info:
            self.model_load_error = "No model selected"
            return False
        
        try:
            dest = self._project_root / "models" / "model.pkl"
            dest.parent.mkdir(exist_ok=True)
            shutil.copy2(info.path, dest)
            self.model_load_error = None
            return True
        except Exception as e:
            self.model_load_error = f"Failed to copy model: {str(e)}"
            return False

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
    
    def increase_n_jobs(self):
        """Increase number of CPUs (up to max)."""
        if self.n_jobs < self.max_cpus:
            self.n_jobs += 1
    
    def decrease_n_jobs(self):
        """Decrease number of CPUs (minimum 1)."""
        if self.n_jobs > 1:
            self.n_jobs -= 1
    
    def get_n_jobs_display(self):
        """Get display string for n_jobs."""
        if self.n_jobs == self.max_cpus:
            return f"{self.n_jobs} CPUs (All)"
        return f"{self.n_jobs} CPUs"
    
    def increase_top_k(self):
        """Increase top-k configurations for tuning."""
        if self.top_k < self.top_k_max:
            self.top_k += 5
    
    def decrease_top_k(self):
        """Decrease top-k configurations for tuning."""
        if self.top_k > self.top_k_min:
            self.top_k -= 5
    
    def increase_cv_folds(self):
        """Increase CV folds."""
        if self.cv_folds < self.cv_folds_max:
            self.cv_folds += 1
    
    def decrease_cv_folds(self):
        """Decrease CV folds."""
        if self.cv_folds > self.cv_folds_min:
            self.cv_folds -= 1

    def start_pipeline(self):
        """Mark pipeline as starting."""
        self.pipeline_running = True
        self.pipeline_complete = False
        self.error_message = None
        self.results_summary = None
        self.results_path = None
        self.current_phase = "baseline"
        self.progress_percent = 0

    def update_step(self, step_name, phase=None, progress=None):
        """Update current pipeline step."""
        self.current_step = step_name
        if phase:
            self.current_phase = phase
        if progress is not None:
            self.progress_percent = min(100, max(0, progress))

    def complete_pipeline(self, results_summary=None, results_path=None):
        """Mark pipeline as complete."""
        self.pipeline_running = False
        self.pipeline_complete = True
        self.results_summary = results_summary
        self.results_path = results_path
        self.current_step = ""
        self.current_phase = ""
        self.progress_percent = 100

    def set_error(self, error_message):
        """Set error message."""
        self.pipeline_running = False
        self.pipeline_complete = False
        self.error_message = error_message
        self.current_step = ""
        self.current_phase = ""
        self.progress_percent = 0
        self.results_path = None
    
    def get_workflow_description(self):
        """Get description of the current workflow configuration."""
        if self.hyperparameter_tuning:
            return (
                f"Two-phase: Baseline → Tune top {self.top_k} "
                f"({self.cv_folds}-fold CV)"
            )
        return "Single-phase: Baseline only"
