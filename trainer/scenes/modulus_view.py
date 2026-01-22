"""View for ModulusScene - handles all rendering."""

import pygame as pg


class ModulusView:
    """View for ModulusScene - handles rendering only, no state modification."""

    def __init__(self, screen):
        self.screen = screen
        self.colors = {
            "white": (255, 255, 255),
            "grey": (40, 40, 40),
            "green": (0, 200, 0),
            "red": (200, 60, 60),
            "yellow": (220, 200, 0),
            "blue": (0, 120, 220),
            "cyan": (0, 180, 180),
            "orange": (220, 140, 0),
            "purple": (140, 80, 200),
            "dark_bg": (15, 15, 18),
            "light_grey": (100, 100, 100),
            "darker_grey": (60, 60, 60),
            "dark_green": (0, 80, 0),
        }

    def draw_text(self, text, x, y, size=28, color=None, center=False):
        """Draw text on the screen."""
        if color is None:
            color = self.colors["white"]
        font = pg.font.SysFont("Arial", size)
        img = font.render(text, True, color)
        rect = img.get_rect()
        if center:
            rect.center = (x, y)
        else:
            rect.topleft = (x, y)
        self.screen.blit(img, rect)
    
    def draw_progress_bar(self, x, y, width, height, progress, color=None):
        """Draw a progress bar."""
        if color is None:
            color = self.colors["green"]
        # Background
        pg.draw.rect(self.screen, self.colors["darker_grey"], (x, y, width, height))
        # Progress
        fill_width = int(width * progress / 100)
        if fill_width > 0:
            pg.draw.rect(self.screen, color, (x, y, fill_width, height))
        # Border
        pg.draw.rect(self.screen, self.colors["light_grey"], (x, y, width, height), 2)

    def render(self, model):
        """Main render method - dispatches to appropriate renderer."""
        if model.error_message:
            self.render_error(model)
        elif model.pipeline_complete:
            self.render_complete(model)
        elif model.pipeline_running:
            self.render_running(model)
        elif model.view_mode == "browse":
            self.render_model_browser(model)
        else:
            self.render_menu(model)

    def render_menu(self, model):
        """Render the experiment configuration menu."""
        W, H = self.screen.get_size()
        self.screen.fill(self.colors["dark_bg"])

        # Title
        self.draw_text(
            "Modulus ML Pipeline",
            W // 2,
            30,
            36,
            self.colors["white"],
            True,
        )
        
        # Tab indicator
        self.draw_text(
            "[B] Browse Models    [Experiments Mode Active]",
            W // 2,
            60,
            16,
            self.colors["light_grey"],
            True,
        )

        # Experiment Mode Selection
        self.draw_text("Experiment Mode:", W // 2, 95, 24, self.colors["yellow"], True)

        y_offset = 120
        mode_labels = {
            "binary": "Binary (Forward vs Rest)",
            "multiclass": "Multiclass (4 Directions)",
            "both": "Both (Binary + Multiclass)",
        }

        for i, mode in enumerate(model.experiment_modes):
            color = (
                self.colors["green"]
                if i == model.selected_mode_index
                else self.colors["light_grey"]
            )
            prefix = "> " if i == model.selected_mode_index else "  "
            label = mode_labels.get(mode, mode.capitalize())
            self.draw_text(
                f"{prefix}{label}",
                W // 2,
                y_offset + i * 28,
                20,
                color,
                True,
            )

        # Options Section
        options_y = y_offset + len(model.experiment_modes) * 28 + 15
        self.draw_text("Options:", W // 2, options_y, 24, self.colors["yellow"], True)

        # Quick Mode
        quick_color = (
            self.colors["green"] if model.quick_mode else self.colors["light_grey"]
        )
        quick_prefix = "[X] " if model.quick_mode else "[ ] "
        self.draw_text(
            f"{quick_prefix}Quick Mode (fewer experiments)",
            W // 2,
            options_y + 28,
            18,
            quick_color,
            True,
        )

        # Hyperparameter Tuning
        tuning_color = (
            self.colors["green"]
            if model.hyperparameter_tuning
            else self.colors["light_grey"]
        )
        tuning_prefix = "[X] " if model.hyperparameter_tuning else "[ ] "
        self.draw_text(
            f"{tuning_prefix}Hyperparameter Tuning (two-phase)",
            W // 2,
            options_y + 50,
            18,
            tuning_color,
            True,
        )
        
        # Show tuning parameters only if tuning is enabled
        tuning_params_y = options_y + 72
        if model.hyperparameter_tuning:
            # Top-K selection
            self.draw_text(
                f"    Top-K configs to tune: {model.top_k}",
                W // 2,
                tuning_params_y,
                16,
                self.colors["cyan"],
                True,
            )
            # CV folds
            self.draw_text(
                f"    CV Folds: {model.cv_folds}",
                W // 2,
                tuning_params_y + 20,
                16,
                self.colors["cyan"],
                True,
            )
            tuning_params_y += 45
        else:
            tuning_params_y += 5
        
        # CPU Count
        cpu_color = self.colors["green"]
        self.draw_text(
            f"Parallel CPUs: {model.get_n_jobs_display()}",
            W // 2,
            tuning_params_y,
            18,
            cpu_color,
            True,
        )
        
        # Workflow description
        workflow_y = tuning_params_y + 25
        self.draw_text(
            f"Workflow: {model.get_workflow_description()}",
            W // 2,
            workflow_y,
            16,
            self.colors["light_grey"],
            True,
        )

        # Controls Section
        controls_y = H - 160
        self.draw_text(
            "[UP/DOWN] Select mode    [Q] Quick    [H] Tuning",
            W // 2,
            controls_y,
            16,
            self.colors["white"],
            True,
        )
        
        # Tuning-specific controls
        if model.hyperparameter_tuning:
            self.draw_text(
                "[T/Y] Top-K ±5    [F/G] CV Folds ±1    [+/-] CPUs",
                W // 2,
                controls_y + 20,
                16,
                self.colors["cyan"],
                True,
            )
        else:
            self.draw_text(
                "[+/-] Adjust CPU count",
                W // 2,
                controls_y + 20,
                16,
                self.colors["white"],
                True,
            )
        
        self.draw_text(
            "[ENTER] Run experiments    [B] Browse models",
            W // 2,
            controls_y + 50,
            20,
            self.colors["green"],
            True,
        )
        self.draw_text(
            "[ESC] Back to menu",
            W // 2,
            controls_y + 78,
            18,
            self.colors["yellow"],
            True,
        )

    def render_model_browser(self, model):
        """Render the model browser view."""
        W, H = self.screen.get_size()
        self.screen.fill(self.colors["dark_bg"])

        # Title
        self.draw_text(
            "Model Browser",
            W // 2,
            30,
            36,
            self.colors["white"],
            True,
        )
        
        # Tab indicator
        self.draw_text(
            "[B] Run Experiments    [Browse Mode Active]",
            W // 2,
            60,
            16,
            self.colors["light_grey"],
            True,
        )
        
        # Model count
        total = len(model.available_models)
        if total == 0:
            self.draw_text(
                "No trained models found",
                W // 2,
                H // 2 - 50,
                24,
                self.colors["light_grey"],
                True,
            )
            self.draw_text(
                "Run experiments first to train models",
                W // 2,
                H // 2,
                18,
                self.colors["light_grey"],
                True,
            )
        else:
            # Header
            self.draw_text(
                f"Available Models: {total}",
                W // 2,
                85,
                20,
                self.colors["yellow"],
                True,
            )
            
            # Scroll indicator
            if total > model.models_per_page:
                scroll_text = f"[{model.browse_scroll_offset + 1}-{min(model.browse_scroll_offset + model.models_per_page, total)} of {total}]"
                self.draw_text(
                    scroll_text,
                    W // 2,
                    105,
                    14,
                    self.colors["light_grey"],
                    True,
                )
            
            # Model list
            visible_models = model.get_visible_models()
            list_start_y = 130
            item_height = 50
            
            for i, info in enumerate(visible_models):
                actual_index = model.browse_scroll_offset + i
                is_selected = actual_index == model.selected_model_index
                
                y = list_start_y + i * item_height
                
                # Selection highlight
                if is_selected:
                    pg.draw.rect(
                        self.screen,
                        self.colors["dark_green"],
                        (50, y - 5, W - 100, item_height - 5),
                        border_radius=5,
                    )
                    pg.draw.rect(
                        self.screen,
                        self.colors["green"],
                        (50, y - 5, W - 100, item_height - 5),
                        2,
                        border_radius=5,
                    )
                
                # Source indicator
                source_color = self.colors["cyan"] if info.source == "experiments" else self.colors["orange"]
                source_label = "📁 EXP" if info.source == "experiments" else "📦 MDL"
                self.draw_text(source_label, 70, y + 5, 14, source_color, False)
                
                # Model name (truncate if too long)
                name = info.name
                if len(name) > 50:
                    name = name[:47] + "..."
                name_color = self.colors["white"] if is_selected else self.colors["light_grey"]
                self.draw_text(name, 140, y + 3, 18, name_color, False)
                
                # Metrics (if available)
                metrics_str = ""
                if info.accuracy is not None:
                    metrics_str += f"Acc: {info.accuracy:.2%}  "
                if info.f1_score is not None:
                    metrics_str += f"F1: {info.f1_score:.2%}"
                if metrics_str:
                    self.draw_text(metrics_str, 140, y + 24, 14, self.colors["cyan"], False)
                elif info.preprocessing:
                    # Show preprocessing if no metrics
                    prep_str = info.preprocessing
                    if len(prep_str) > 40:
                        prep_str = prep_str[:37] + "..."
                    self.draw_text(prep_str, 140, y + 24, 14, self.colors["light_grey"], False)
            
            # Selected model details
            selected_info = model.get_selected_model_info()
            if selected_info:
                details_y = list_start_y + model.models_per_page * item_height + 10
                
                # Separator line
                pg.draw.line(
                    self.screen,
                    self.colors["darker_grey"],
                    (50, details_y),
                    (W - 50, details_y),
                    2,
                )
                
                details_y += 15
                self.draw_text("Selected Model Details:", 60, details_y, 16, self.colors["yellow"], False)
                details_y += 22
                
                if selected_info.model_type:
                    self.draw_text(f"Model: {selected_info.model_type}", 70, details_y, 14, self.colors["white"], False)
                    details_y += 18
                if selected_info.preprocessing:
                    prep = selected_info.preprocessing
                    if len(prep) > 60:
                        prep = prep[:57] + "..."
                    self.draw_text(f"Preprocessing: {prep}", 70, details_y, 14, self.colors["white"], False)
                    details_y += 18
                if selected_info.split_ratio:
                    self.draw_text(f"Split: {selected_info.split_ratio}", 70, details_y, 14, self.colors["white"], False)
                    details_y += 18
                
                # Path (truncated)
                path_str = str(selected_info.path)
                if len(path_str) > 70:
                    path_str = "..." + path_str[-67:]
                self.draw_text(f"Path: {path_str}", 70, details_y, 12, self.colors["light_grey"], False)
        
        # Loaded model indicator
        if model.loaded_model_info:
            self.draw_text(
                f"✓ Loaded & Ready for Driving: {model.loaded_model_info.name[:35]}",
                W // 2,
                H - 130,
                16,
                self.colors["green"],
                True,
            )
        
        # Error message
        if model.model_load_error:
            self.draw_text(
                model.model_load_error,
                W // 2,
                H - 110,
                16,
                self.colors["red"],
                True,
            )

        # Controls
        controls_y = H - 85
        self.draw_text(
            "[UP/DOWN] Navigate    [ENTER] Load model    [C] Copy to model.pkl",
            W // 2,
            controls_y,
            16,
            self.colors["white"],
            True,
        )
        self.draw_text(
            "[R] Refresh list    [B] Back to experiments    [ESC] Exit",
            W // 2,
            controls_y + 22,
            16,
            self.colors["yellow"],
            True,
        )

    def render_running(self, model):
        """Render pipeline execution screen."""
        W, H = self.screen.get_size()
        self.screen.fill(self.colors["dark_bg"])

        # Title
        self.draw_text(
            "Running ML Pipeline", W // 2, 80, 36, self.colors["white"], True
        )
        
        # Phase indicator
        phase_color = self.colors["cyan"] if model.current_phase == "tuning" else self.colors["yellow"]
        phase_text = {
            "baseline": "Phase 1: Baseline Validation",
            "tuning": "Phase 2: Hyperparameter Tuning",
        }.get(model.current_phase, "Processing")
        self.draw_text(phase_text, W // 2, 130, 24, phase_color, True)

        # Progress bar
        bar_width = 400
        bar_height = 25
        bar_x = (W - bar_width) // 2
        bar_y = H // 2 - 50
        self.draw_progress_bar(bar_x, bar_y, bar_width, bar_height, model.progress_percent)
        
        # Progress percentage
        self.draw_text(
            f"{model.progress_percent}%",
            W // 2,
            bar_y + bar_height + 20,
            20,
            self.colors["white"],
            True,
        )

        # Current step
        if model.current_step:
            self.draw_text(
                model.current_step, W // 2, H // 2 + 30, 22, self.colors["green"], True
            )

        # Loading indicator
        import time
        dots = "." * (int(time.time() * 2) % 4)
        self.draw_text(
            f"Processing{dots}", W // 2, H // 2 + 70, 20, self.colors["light_grey"], True
        )

        # Instructions
        self.draw_text(
            "[ESC] Cancel (may take a moment)",
            W // 2,
            H - 80,
            18,
            self.colors["light_grey"],
            True,
        )

    def render_complete(self, model):
        """Render pipeline completion screen."""
        W, H = self.screen.get_size()
        self.screen.fill(self.colors["dark_bg"])

        # Title
        self.draw_text(
            "✓ Pipeline Complete!", W // 2, 80, 36, self.colors["green"], True
        )

        # Results summary
        y_offset = 150
        if model.results_path:
            self.draw_text(
                "Results saved to:",
                W // 2,
                y_offset,
                22,
                self.colors["white"],
                True,
            )
            # Handle long paths
            path_str = str(model.results_path)
            if len(path_str) > 60:
                path_str = "..." + path_str[-57:]
            self.draw_text(
                path_str,
                W // 2,
                y_offset + 28,
                18,
                self.colors["green"],
                True,
            )
            y_offset += 70

        if model.results_summary:
            for line in model.results_summary.split("\n"):
                if line.strip() and len(line.strip()) < 80:
                    self.draw_text(
                        line.strip(), W // 2, y_offset, 18, self.colors["white"], True
                    )
                    y_offset += 24
                    if y_offset > H - 140:
                        break

        # Instructions
        self.draw_text(
            "[B] Browse models    [ESC] Back to menu",
            W // 2,
            H - 80,
            24,
            self.colors["yellow"],
            True,
        )

    def render_error(self, model):
        """Render error screen."""
        W, H = self.screen.get_size()
        self.screen.fill(self.colors["dark_bg"])

        # Title
        self.draw_text("✗ Error", W // 2, 80, 36, self.colors["red"], True)

        # Error message
        if model.error_message:
            # Wrap long error messages
            words = model.error_message.split()
            lines = []
            current_line = ""
            for word in words:
                test_line = current_line + " " + word if current_line else word
                if len(test_line) < 60:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)

            y_offset = 180
            for line in lines[:10]:  # Limit to 10 lines
                self.draw_text(line, W // 2, y_offset, 18, self.colors["white"], True)
                y_offset += 24

        # Instructions
        self.draw_text(
            "[ESC] Back to menu",
            W // 2,
            H - 80,
            24,
            self.colors["yellow"],
            True,
        )
