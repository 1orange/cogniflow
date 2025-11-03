import os
import time
import numpy as np
import random
import pygame as pg
from concurrent.futures import ThreadPoolExecutor
from config import *
from bci.utils import LABELS
from trainer.scenes.base_scene import BaseScene


class RecordScene(BaseScene):
    """Handles the BCI data recording process for raw data collection."""

    def __init__(self, screen, clock, source):
        super().__init__(screen, clock)
        self.source = source
        self.executor = ThreadPoolExecutor(max_workers=1)

    def run(self):
        """Run the data recording process."""
        W, H = self.screen.get_size()
        
        # Step 1: Select directions to record
        selected_directions = self._select_directions()
        if not selected_directions:
            return  # User cancelled
        
        # Step 2: Set recording window size
        window_duration = self._select_window_duration()
        if window_duration is None:
            return  # User cancelled
        
        # Step 3: Set number of trials per direction
        trials_per_direction = self._select_trials_count()
        if trials_per_direction is None:
            return  # User cancelled
        
        # Now proceed with recording
        self._record_data(selected_directions, window_duration, trials_per_direction)
    
    def _select_directions(self):
        """Allow user to select which directions to record."""
        W, H = self.screen.get_size()
        selected = {label: True for label in LABELS}  # All selected by default
        running = True
        
        while running:
            self.screen.fill(self.colors["grey"])
            self.draw_text("Select Directions to Record", W // 2, 60, 40, self.colors["white"], True)
            self.draw_text("Press 1-4 to toggle directions", W // 2, 110, 24, self.colors["yellow"], True)
            self.draw_text("Press ENTER to continue or ESC to cancel", W // 2, 140, 20, self.colors["white"], True)
            
            # Draw direction options in a grid
            y_start = 200
            y_spacing = 80
            
            for i, label in enumerate(LABELS):
                y = y_start + i * y_spacing
                color = self.colors["green"] if selected[label] else self.colors["red"]
                status = "✓" if selected[label] else "✗"
                self.draw_text(f"[{i+1}] {status} {label.upper()}", W // 2, y, 32, color, True)
            
            # Instructions
            self.draw_text(f"Selected: {sum(selected.values())}/{len(LABELS)}", W // 2, H - 80, 24, self.colors["yellow"], True)
            
            for e in pg.event.get():
                if e.type == pg.QUIT or (e.type == pg.KEYDOWN and e.key == pg.K_ESCAPE):
                    return []
                elif e.type == pg.KEYDOWN:
                    if e.key == pg.K_RETURN:
                        result = [label for label, is_selected in selected.items() if is_selected]
                        if result:
                            return result
                    elif e.key == pg.K_1:
                        selected[LABELS[0]] = not selected[LABELS[0]]
                    elif e.key == pg.K_2:
                        selected[LABELS[1]] = not selected[LABELS[1]]
                    elif e.key == pg.K_3:
                        selected[LABELS[2]] = not selected[LABELS[2]]
                    elif e.key == pg.K_4:
                        selected[LABELS[3]] = not selected[LABELS[3]]
            
            pg.display.flip()
            self.clock.tick(60)
        
        return []
    
    def _select_window_duration(self):
        """Allow user to set the recording window duration."""
        W, H = self.screen.get_size()
        duration = TASK_SEC  # Default
        running = True
        
        while running:
            self.screen.fill(self.colors["grey"])
            self.draw_text("Set Recording Window Duration", W // 2, 60, 40, self.colors["white"], True)
            self.draw_text("How long should each trial last?", W // 2, 110, 24, self.colors["yellow"], True)
            
            # Show current duration
            self.draw_text(f"Duration: {duration:.1f} seconds", W // 2, H // 2 - 40, 48, self.colors["green"], True)
            
            # Instructions
            self.draw_text("Use UP/DOWN arrows to adjust (0.5s steps)", W // 2, H // 2 + 40, 24, self.colors["white"], True)
            self.draw_text("Use LEFT/RIGHT arrows for fine adjustment (0.1s steps)", W // 2, H // 2 + 70, 20, self.colors["white"], True)
            self.draw_text("Press ENTER to continue or ESC to cancel", W // 2, H // 2 + 110, 20, self.colors["yellow"], True)
            
            for e in pg.event.get():
                if e.type == pg.QUIT or (e.type == pg.KEYDOWN and e.key == pg.K_ESCAPE):
                    return None
                elif e.type == pg.KEYDOWN:
                    if e.key == pg.K_RETURN:
                        return duration
                    elif e.key == pg.K_UP:
                        duration = min(20.0, duration + 0.5)
                    elif e.key == pg.K_DOWN:
                        duration = max(1.0, duration - 0.5)
                    elif e.key == pg.K_RIGHT:
                        duration = min(20.0, duration + 0.1)
                    elif e.key == pg.K_LEFT:
                        duration = max(1.0, duration - 0.1)
            
            pg.display.flip()
            self.clock.tick(60)
        
        return None
    
    def _select_trials_count(self):
        """Allow user to set number of trials per direction."""
        W, H = self.screen.get_size()
        trials = TRIALS_PER_CLASS  # Default
        running = True
        
        while running:
            self.screen.fill(self.colors["grey"])
            self.draw_text("Set Number of Trials", W // 2, 60, 40, self.colors["white"], True)
            self.draw_text("How many trials per direction?", W // 2, 110, 24, self.colors["yellow"], True)
            
            # Show current count
            self.draw_text(f"Trials: {trials}", W // 2, H // 2 - 40, 48, self.colors["green"], True)
            
            # Instructions
            self.draw_text("Use UP/DOWN arrows to adjust", W // 2, H // 2 + 40, 24, self.colors["white"], True)
            self.draw_text("Press ENTER to continue or ESC to cancel", W // 2, H // 2 + 80, 20, self.colors["yellow"], True)
            
            for e in pg.event.get():
                if e.type == pg.QUIT or (e.type == pg.KEYDOWN and e.key == pg.K_ESCAPE):
                    return None
                elif e.type == pg.KEYDOWN:
                    if e.key == pg.K_RETURN:
                        return trials
                    elif e.key == pg.K_UP:
                        trials = min(50, trials + 1)
                    elif e.key == pg.K_DOWN:
                        trials = max(1, trials - 1)
            
            pg.display.flip()
            self.clock.tick(60)
        
        return None
    
    def _record_data(self, selected_directions, window_duration, trials_per_direction):
        """Perform the actual data recording."""
        W, H = self.screen.get_size()
        fs = SAMPLE_RATE
        n_ch = N_CHANNELS
        win_len = int(WIN_SEC * fs)
        hop = int(HOP_SEC * fs)
        chan_buf = np.zeros((0, n_ch))

        # Data storage structure - only for selected directions
        recorded_data = {lab: [] for lab in selected_directions}
        order = []
        [order.extend([lab] * trials_per_direction) for lab in selected_directions]
        random.shuffle(order)

        self.source.start()
        trial_idx = 0
        phase = "baseline"
        t0 = time.time()
        intended = order[trial_idx]
        if hasattr(self.source, "set_intended_label"):
            self.source.set_intended_label(None)
        running = True

        try:
            while running:
                dt = self.clock.tick(60) / 1000.0
                elapsed = time.time() - t0
                total = (
                    BASELINE_SEC
                    if phase == "baseline"
                    else window_duration  # Use the user-selected duration
                    if phase == "task"
                    else REST_SEC
                )
                remaining = max(0.0, total - elapsed)

                self.screen.fill(self.colors["grey"])
                self.draw_text("Data Recording", W // 2, 40, 40, self.colors["white"], True)
                self.draw_text(
                    f"Trial {trial_idx + 1}/{len(order)} | Direction: {intended}",
                    W // 2,
                    90,
                    28,
                    self.colors["yellow"],
                    True,
                )
                
                # Display current phase
                phase_text = phase.upper()
                phase_color = (
                    self.colors["blue"] if phase == "task"
                    else self.colors["white"]
                )
                self.draw_text(
                    f"Phase: {phase_text}",
                    W // 2,
                    130,
                    32,
                    phase_color,
                    True,
                )

                # Progress bar
                pg.draw.rect(
                    self.screen, self.colors["white"], (W * 0.2, H * 0.9, W * 0.6, 10), 1
                )
                pg.draw.rect(
                    self.screen,
                    self.colors["blue"] if phase == "task" else self.colors["white"],
                    (W * 0.2, H * 0.9, W * 0.6 * (1 - remaining / total), 10),
                )

                if phase == "task":
                    # Draw arrow for current task
                    arrow_surf = self.arrow_surface(intended, 160, self.colors["white"])
                    self.screen.blit(arrow_surf, (W // 2 - 80, H // 2 - 80))
                    if hasattr(self.source, "set_intended_label"):
                        self.source.set_intended_label(intended)
                else:
                    if hasattr(self.source, "set_intended_label"):
                        self.source.set_intended_label(None)

                # Read samples
                n_need = int(dt * fs)
                if n_need > 0:
                    samples = self.source.read(n_need)
                    if samples.shape[1] != n_ch:
                        samples = np.pad(
                            samples, ((0, 0), (0, max(0, n_ch - samples.shape[1])))
                        )[:, :n_ch]
                    chan_buf = np.vstack([chan_buf, samples])
                    if chan_buf.shape[0] > win_len * 3:
                        chan_buf = chan_buf[-win_len * 2 :, :]

                # Process windows during task phase
                if phase == "task":
                    while chan_buf.shape[0] >= win_len:
                        win = chan_buf[:win_len, :]
                        chan_buf = chan_buf[hop:, :]
                        recorded_data[intended].append(win.copy())

                # Phase transitions
                if remaining <= 1e-3:
                    if phase == "baseline":
                        phase = "task"
                        t0 = time.time()
                    elif phase == "task":
                        phase = "rest"
                        t0 = time.time()
                    else:
                        trial_idx += 1
                        if trial_idx >= len(order):
                            running = False
                        else:
                            intended = order[trial_idx]
                            phase = "baseline"
                            t0 = time.time()

                # Handle events
                for e in pg.event.get():
                    if e.type == pg.QUIT or (e.type == pg.KEYDOWN and e.key == pg.K_ESCAPE):
                        running = False

                pg.display.flip()

        finally:
            # Ensure source is always stopped, even if interrupted
            self.source.stop()

        # Show saving message
        self.screen.fill(self.colors["grey"])
        self.draw_text(
            "Saving recorded data...", W // 2, H // 2, 36, self.colors["yellow"], True
        )
        self.draw_text(
            "Please wait", W // 2, H // 2 + 40, 24, self.colors["white"], True
        )
        pg.display.flip()

        # Save data asynchronously
        def save_data_async():
            try:
                # Create data directory if it doesn't exist
                os.makedirs("data", exist_ok=True)

                # Generate timestamp for this recording session
                timestamp = time.strftime("%Y%m%d_%H%M%S")

                # Save data for each direction
                for direction in selected_directions:
                    if recorded_data[direction]:  # Only save if we have data
                        # Convert list of windows to numpy array
                        data_array = np.array(recorded_data[direction])

                        # Create filename with direction and timestamp
                        filename = f"data/recorded_data_{direction}_{timestamp}.npy"

                        # Save the raw data
                        np.save(filename, data_array)

                        # Also save metadata
                        metadata_filename = f"data/metadata_{direction}_{timestamp}.txt"
                        with open(metadata_filename, "w") as f:
                            f.write(f"Direction: {direction}\n")
                            f.write(f"Timestamp: {timestamp}\n")
                            f.write(f"Sample rate: {fs} Hz\n")
                            f.write(f"Channels: {n_ch}\n")
                            f.write(f"Window length: {WIN_SEC} seconds\n")
                            f.write(f"Hop length: {HOP_SEC} seconds\n")
                            f.write(
                                f"Number of windows: {len(recorded_data[direction])}\n"
                            )
                            f.write(f"Data shape: {data_array.shape}\n")

                return True
            except Exception as e:
                print(f"Data saving error: {e}")
                return False

        # Submit saving task
        saving_future = self.executor.submit(save_data_async)

        # Wait for saving to complete with progress indication
        while not saving_future.done():
            # Show animated progress
            dots = "." * (int(time.time() * 2) % 4)
            self.screen.fill(self.colors["grey"])
            self.draw_text(
                "Saving data" + dots, W // 2, H // 2, 36, self.colors["yellow"], True
            )
            self.draw_text(
                "Please wait", W // 2, H // 2 + 40, 24, self.colors["white"], True
            )
            pg.display.flip()
            time.sleep(0.1)

        # Get saving result
        success = saving_future.result()

        # Show completion screen
        self.screen.fill(self.colors["grey"])
        if success:
            self.draw_text(
                "Data recording complete",
                W // 2,
                H // 2 - 40,
                36,
                self.colors["green"],
                True,
            )
            self.draw_text(
                "Raw data saved to /data folder",
                W // 2,
                H // 2 + 10,
                28,
                self.colors["white"],
                True,
            )

            # Show summary of recorded data
            total_windows = sum(len(recorded_data[direction]) for direction in selected_directions)
            self.draw_text(
                f"Total windows recorded: {total_windows}",
                W // 2,
                H // 2 + 50,
                24,
                self.colors["white"],
                True,
            )
        else:
            self.draw_text(
                "Error saving data", W // 2, H // 2 - 40, 36, self.colors["red"], True
            )
            self.draw_text(
                "Check console for details",
                W // 2,
                H // 2 + 10,
                28,
                self.colors["white"],
                True,
            )

        self.draw_text(
            "Press ESC to return", W // 2, H // 2 + 100, 24, self.colors["yellow"], True
        )
        pg.display.flip()

        waiting = True
        try:
            while waiting:
                for e in pg.event.get():
                    if e.type == pg.QUIT or (
                        e.type == pg.KEYDOWN and e.key == pg.K_ESCAPE
                    ):
                        waiting = False
                self.clock.tick(30)
        finally:
            # Cleanup
            self.executor.shutdown(wait=True)
