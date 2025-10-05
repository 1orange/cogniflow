import os
import time
import numpy as np
import random
import pygame as pg
from concurrent.futures import ThreadPoolExecutor
from config import *
from bci.utils import LABELS
from trainer.scenes.base_scene import BaseScene


class CalibrationScene(BaseScene):
    """Handles the BCI calibration process."""

    def __init__(self, screen, clock, source):
        super().__init__(screen, clock)
        self.source = source
        self.executor = ThreadPoolExecutor(max_workers=1)

    def run(self):
        """Run the calibration process."""
        W, H = self.screen.get_size()
        fs = SAMPLE_RATE
        n_ch = N_CHANNELS
        win_len = int(WIN_SEC * fs)
        hop = int(HOP_SEC * fs)
        chan_buf = np.zeros((0, n_ch))
        windows = {lab: [] for lab in LABELS}
        order = []
        [order.extend([lab] * TRIALS_PER_CLASS) for lab in LABELS]
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
                    else TASK_SEC
                    if phase == "task"
                    else REST_SEC
                )
                remaining = max(0.0, total - elapsed)

                self.screen.fill(self.colors["grey"])
                self.draw_text("Calibration", W // 2, 40, 40, self.colors["white"], True)
                self.draw_text(
                    f"Trial {trial_idx + 1}/{len(order)} | Label: {intended}",
                    W // 2,
                    90,
                    28,
                    self.colors["yellow"],
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
                        windows[intended].append(win.copy())

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

        # Show training message
        self.screen.fill(self.colors["grey"])
        self.draw_text(
            "Training model...", W // 2, H // 2, 36, self.colors["yellow"], True
        )
        self.draw_text(
            "Please wait", W // 2, H // 2 + 40, 24, self.colors["white"], True
        )
        pg.display.flip()

        # Train model asynchronously
        def train_model_async():
            ...

        # Submit training task
        training_future = self.executor.submit(train_model_async)

        # Wait for training to complete with progress indication
        while not training_future.done():
            # Show animated progress
            dots = "." * (int(time.time() * 2) % 4)
            self.screen.fill(self.colors["grey"])
            self.draw_text(
                "Training model" + dots, W // 2, H // 2, 36, self.colors["yellow"], True
            )
            self.draw_text(
                "Please wait", W // 2, H // 2 + 40, 24, self.colors["white"], True
            )
            pg.display.flip()
            time.sleep(0.1)

        # Get training result
        bal = training_future.result()

        # Show completion screen
        self.screen.fill(self.colors["grey"])
        self.draw_text(
            "Training complete", W // 2, H // 2 - 40, 36, self.colors["green"], True
        )
        self.draw_text(
            f"Hold-out balanced acc: {bal:.2f}",
            W // 2,
            H // 2 + 10,
            28,
            self.colors["white"],
            True,
        )
        self.draw_text(
            "Press ESC to return", W // 2, H // 2 + 60, 24, self.colors["yellow"], True
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
