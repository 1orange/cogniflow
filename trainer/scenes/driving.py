import pygame as pg
import numpy as np
import time
import os
import random
import threading
import math
from collections import deque
from concurrent.futures import ThreadPoolExecutor

from config import *
from bci.utils import LABELS, majority_vote
from trainer.scenes.base_scene import BaseScene
from trainer.utils.car import Car


class DrivingScene(BaseScene):
    """Main driving scene that manages the trainer state, rendering, and input handling.
    Renders everything to a fixed 320x180 'world' surface, then scales it to the window.
    """

    def __init__(self, screen, clock, source=None, model_path=None, control_mode="bci"):
        super().__init__(screen, clock)
        self.source = source
        self.model_path = model_path
        self.model = None

        # Game state
        self.control_mode = control_mode  # 'bci' or 'arrow'

        # Car (pseudo-3D position, matches your existing Car)
        self.car = Car(x=0, y=300, z=0)

        # BCI control variables
        self.last_cmd = None
        self.dead_until = 0.0
        self.consecutive = 0
        self.hist = deque(maxlen=MAJORITY_K)
        self.win_len = int(WIN_SEC * SAMPLE_RATE)
        self.hop = int(HOP_SEC * SAMPLE_RATE)
        self.chan_buf = np.zeros((0, N_CHANNELS))
        self.mv = None
        self.active_commands = []  # Track currently active commands

        # Gate system
        self.gate_every = 5.0
        self.t_last_gate = time.time() - self.gate_every
        self.gate_label = None
        self.gate_timeout = 2.0

        # Async preprocessing
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.bci_lock = threading.Lock()
        self.pending_bci_result = None
        self.bci_processing = False

        # Off-screen low-res render target (virtual resolution)
        self.world = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

        self._load_sprites()

    # ----------------------------
    # Assets
    # ----------------------------
    def _load_sprites(self):
        base = os.path.join(os.path.dirname(__file__), "..", "assets")
        self.road_sprite = pg.image.load(os.path.join(base, "road.png")).convert()

        # Load car sprite with proper alpha handling
        self.car_sprite = pg.image.load(os.path.join(base, "car.png")).convert()

        # Set colorkey BEFORE converting to alpha - this properly handles transparency
        car_img.set_colorkey((255, 0, 255))

        # Get original dimensions to maintain aspect ratio
        orig_width, orig_height = car_img.get_size()
        target_width = 80
        target_height = int(target_width * orig_height / orig_width)

        self.mountains_sprite = pg.image.load(
            os.path.join(base, "mountains.png")
        ).convert()

    # ----------------------------
    # Road math (virtual space)
    # ----------------------------
    def calculate_road_curve_y(self, road_position_x):
        return ROAD_CURVE_AMPLITUDE_1 * math.sin(
            road_position_x / ROAD_CURVE_FREQUENCY_1
        ) + ROAD_CURVE_AMPLITUDE_2 * math.sin(road_position_x / ROAD_CURVE_FREQUENCY_2)

    def calculate_road_incline_z(self, road_position_x):
        return ROAD_INCLINE_BASE
        # return (
        #     ROAD_INCLINE_BASE
        #     + ROAD_INCLINE_AMPLITUDE_1
        #     * math.sin(road_position_x / ROAD_INCLINE_FREQUENCY_1)
        #     - ROAD_INCLINE_AMPLITUDE_2
        #     * math.sin(road_position_x / ROAD_INCLINE_FREQUENCY_2)
        # )

    # ----------------------------
    # Rendering helpers (virtual space)
    # ----------------------------
    def render_road_element(
        self,
        surface,
        sprite,
        width,
        height,
        road_scale,
        road_position_x,
        player_y,
        z_buffer,
    ):
        """All coords in 320x180 virtual space."""
        element_y = self.calculate_road_curve_y(road_position_x) - player_y
        element_z = self.calculate_road_incline_z(road_position_x) - self.car.z

        screen_vertical = int(
            ROAD_BASE_HEIGHT + ROAD_SCALE_FACTOR * road_scale + element_z * road_scale
        )

        if (
            1 <= screen_vertical < SCREEN_HEIGHT
            and z_buffer[screen_vertical - 1] > 1 / road_scale - 10
        ):
            screen_horizontal = (
                160
                - (160 - element_y) * road_scale
                + self.car.angle * (screen_vertical - 150)
            )

            w = max(1, int(width))
            h = max(1, int(height))
            # Use smoothscale for higher quality at the cost of some performance
            scaled_sprite = pg.transform.smoothscale(sprite, (w, h))
            surface.blit(
                scaled_sprite, (int(screen_horizontal), int(screen_vertical - h + 1))
            )

    def _prepare_driving_scene(self, total_time):
        """Draw one full frame into self.world (virtual space only)."""
        # Clear virtual screen
        self.world.fill(self.colors["dark_bg"])

        # Background mountains (parallax) in virtual coords
        self.world.blit(self.mountains_sprite, (-65 - self.car.angle * 82, 0))

        # Car height above road
        self.car.z = self.calculate_road_incline_z(self.car.x)

        # Road rendering
        screen_vertical = SCREEN_HEIGHT
        road_draw_distance = 1
        z_buffer = [999 for _ in range(SCREEN_HEIGHT)]

        while road_draw_distance < ROAD_DRAW_DISTANCE:
            last_screen_vertical = screen_vertical

            while (
                screen_vertical >= last_screen_vertical
                and road_draw_distance < ROAD_DRAW_DISTANCE
            ):
                road_draw_distance += road_draw_distance / ROAD_PERSPECTIVE_FACTOR
                road_position_x = self.car.x + road_draw_distance
                road_scale = 1 / road_draw_distance
                road_incline_z = (
                    self.calculate_road_incline_z(road_position_x) - self.car.z
                )
                screen_vertical = int(
                    ROAD_BASE_HEIGHT
                    + ROAD_SCALE_FACTOR * road_scale
                    + road_incline_z * road_scale
                )

            if road_draw_distance < ROAD_DRAW_DISTANCE:
                sv = max(0, min(SCREEN_HEIGHT - 1, int(screen_vertical)))
                z_buffer[sv] = road_draw_distance

                # Texture slice (1px high) in virtual space
                slice_y = int(10 * road_position_x) % 360
                road_slice = self.road_sprite.subsurface((0, slice_y, SCREEN_WIDTH, 1))

                road_color = (
                    int(
                        ROAD_COLOR_BASE[0]
                        - road_draw_distance / ROAD_COLOR_DISTANCE_FACTOR
                    ),
                    int(ROAD_COLOR_BASE[1] - road_draw_distance),
                    int(
                        ROAD_COLOR_BASE[2]
                        - road_incline_z / ROAD_COLOR_Z_FACTOR
                        + ROAD_COLOR_SINE_FACTOR * math.sin(road_position_x)
                    ),
                )

                # Draw the strip (virtual pixels)
                pg.draw.rect(self.world, road_color, (0, sv, SCREEN_WIDTH, 1))

                # Optional: roadside element demo (using the strip as a faux sprite)
                self.render_road_element(
                    self.world,
                    road_slice,
                    500 * road_scale,
                    1,
                    road_scale,
                    road_position_x,
                    self.car.y,
                    z_buffer,
                )

        # Player car with bobbing (virtual space)
        self.world.blit(
            self.car_sprite, (120, 120 + math.sin(total_time * self.car.velocity))
        )

        # Collision indicator (virtual space)
        road_curve_y = self.calculate_road_curve_y(self.car.x + 2)
        if (
            abs(self.car.y - road_curve_y - 100) > COLLISION_THRESHOLD
            and self.car.velocity > COLLISION_MIN_VELOCITY
        ):
            # Use a tiny fixed dt for 'impact' damping to keep behavior consistent
            self.car.velocity += -self.car.velocity * 0.016
            self.car.acceleration += -self.car.acceleration * 0.016
            pg.draw.circle(self.world, (255, 0, 0), (300, 170), 3)

    # ----------------------------
    # UI (drawn in window space so it stays crisp)
    # ----------------------------
    def draw_ui(self, W, H, tnow):
        # Title
        self.draw_text("Drive", 20, 20, 32, self.colors["white"])

        # Control mode indicator
        mode_color = (
            self.colors["green"]
            if self.control_mode == "arrow"
            else self.colors["blue"]
        )
        self.draw_text(f"Mode: {self.control_mode.upper()}", 20, 50, 24, mode_color)

        # Active commands display
        if self.active_commands:
            commands_text = ", ".join(self.active_commands)
            self.draw_text(f"Active: {commands_text}", 20, 80, 24, self.colors["green"])
        else:
            self.draw_text("Active: None", 20, 80, 24, self.colors["white"])

        # BCI info
        if self.control_mode == "bci":
            self.draw_text(
                f"Last: {self.last_cmd if self.last_cmd else 'None'}",
                20,
                110,
                24,
                self.colors["yellow"],
            )
            self.draw_text(
                f"Conf: {self.mv[1]:.2f}" if self.mv else "Conf: --",
                20,
                140,
                24,
                self.colors["yellow"],
            )

        # Speed
        self.draw_text(
            f"Speed: {int(self.car.speed)}", 20, 170, 24, self.colors["white"]
        )

        # Gate target (only show briefly)
        if self.control_mode == "bci":
            if self.gate_label and (tnow - self.t_last_gate) < self.gate_timeout:
                self.screen.blit(
                    self.arrow_surface(self.gate_label, 120, self.colors["white"]),
                    (W - 160, 40),
                )
            else:
                self.gate_label = None

        # Instructions
        self.draw_text("ESC: back", W - 100, H - 40, 20, self.colors["white"])

    # ----------------------------
    # Input
    # ----------------------------
    def handle_arrow_input(self, keys):
        commands = []
        if keys[pg.K_LEFT]:
            commands.append("left")
        if keys[pg.K_RIGHT]:
            commands.append("right")
        if keys[pg.K_UP]:
            commands.append("forward")
        if keys[pg.K_DOWN]:
            commands.append("backward")
        return commands

    # ----------------------------
    # BCI
    # ----------------------------
    def _process_bci_async(self, win, tnow):
        try:
            proba = None

            if proba is not None:
                active_commands = []
                for label, confidence in proba.items():
                    if confidence >= CONF_THRESHOLD:
                        active_commands.append((label, confidence))
                active_commands.sort(key=lambda x: x[1], reverse=True)

                if active_commands:
                    top_label, top_p = active_commands[0]
                    with self.bci_lock:
                        self.hist.append((top_label, top_p))
                        self.mv = majority_vote(list(self.hist), MAJORITY_K)

                        if self.mv and tnow >= self.dead_until:
                            pred, conf = self.mv
                            self.consecutive = (
                                self.consecutive + 1 if pred == self.last_cmd else 1
                            )
                            if self.consecutive >= TURN_HOLD_FRAMES:
                                self.last_cmd = pred
                                self.dead_until = tnow + DEADZONE_SEC
                                return [
                                    cmd[0]
                                    for cmd in active_commands
                                    if cmd[1] >= CONF_THRESHOLD
                                ]
            return []
        except Exception as e:
            print(f"BCI processing error: {e}")
            return []

    def update_bci_control(self, dt, tnow):
        if not self.source or not self.model:
            return []

        n_need = int(dt * SAMPLE_RATE)
        if n_need > 0:
            samples = self.source.read(n_need)
            if samples.shape[1] != N_CHANNELS:
                samples = np.pad(
                    samples, ((0, 0), (0, max(0, N_CHANNELS - samples.shape[1])))
                )[:, :N_CHANNELS]
            self.chan_buf = np.vstack([self.chan_buf, samples])
            if self.chan_buf.shape[0] > self.win_len * 3:
                self.chan_buf = self.chan_buf[-self.win_len * 2 :, :]

        if self.pending_bci_result and self.pending_bci_result.done():
            try:
                result = self.pending_bci_result.result()
                self.active_commands = result
                self.pending_bci_result = None
                self.bci_processing = False
            except Exception as e:
                print(f"Error getting BCI result: {e}")
                self.pending_bci_result = None
                self.bci_processing = False

        if self.chan_buf.shape[0] >= self.win_len and not self.bci_processing:
            win = self.chan_buf[: self.win_len, :]
            self.chan_buf = self.chan_buf[self.hop :, :]
            self.pending_bci_result = self.executor.submit(
                self._process_bci_async, win, tnow
            )
            self.bci_processing = True

        return self.active_commands

    # ----------------------------
    # Gates
    # ----------------------------
    def update_gate_system(self, tnow):
        if tnow - self.t_last_gate > self.gate_every:
            self.gate_label = random.choice(LABELS)
            self.t_last_gate = tnow

    # ----------------------------
    # Main loop
    # ----------------------------
    def run(self):
        """Main trainer loop."""
        # Only start BCI source if using BCI control mode
        if self.source and self.control_mode == "bci":
            self.source.start()

        self.running = True
        total_time = 0

        try:
            while self.running:
                dt = self.clock.tick(60) / 1000.0
                tnow = time.time()
                total_time += dt

                for event in pg.event.get():
                    if event.type == pg.QUIT:
                        self.running = False
                    elif event.type == pg.KEYDOWN:
                        if event.key == pg.K_ESCAPE:
                            self.running = False

                # Controls
                if self.control_mode == "arrow":
                    keys = pg.key.get_pressed()
                    commands = self.handle_arrow_input(keys)
                else:
                    commands = self.update_bci_control(dt, tnow)

                self.active_commands = commands

                # Physics update
                self.car.update(dt, commands)

                # Gates
                self.update_gate_system(tnow)

                # ---- Render to virtual world ----
                self._prepare_driving_scene(total_time)

                # ---- Scale once to the real window (with auto letterboxing to preserve aspect) ----
                W, H = self.screen.get_size()
                self.screen.fill(self.colors["dark_bg"])

                target_aspect = SCREEN_WIDTH / SCREEN_HEIGHT
                win_aspect = W / H
                if win_aspect > target_aspect:
                    h = H
                    w = int(h * target_aspect)
                    x, y = (W - w) // 2, 0
                else:
                    w = W
                    h = int(w / target_aspect)
                    x, y = 0, (H - h) // 2

                scaled = pg.transform.scale(self.world, (w, h))
                self.screen.blit(scaled, (x, y))

                # UI in window space (stays crisp)
                self.draw_ui(W, H, tnow)

                pg.display.flip()

        finally:
            # Stop source only if it was started (BCI mode)
            if self.source and self.control_mode == "bci":
                self.source.stop()
            self.executor.shutdown(wait=True)
