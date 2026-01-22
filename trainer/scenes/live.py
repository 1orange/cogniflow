"""LiveScene - Real-time BCI prediction to MQTT following MVC architecture."""

import pygame as pg
import numpy as np
import time
import threading
import logging
from pathlib import Path
from datetime import datetime
from collections import deque
from concurrent.futures import ThreadPoolExecutor

from config import SAMPLE_RATE, N_CHANNELS, WIN_SEC, HOP_SEC, CONF_THRESHOLD, MAJORITY_K
from bci.utils import majority_vote
from trainer.scenes.base_scene import BaseScene
from trainer.scenes.live_model import LiveModel
from trainer.scenes.live_view import LiveView
from trainer.scenes.live_controller import LiveController
from trainer.model_store import model_store


def setup_live_logger():
    """Setup logger for live scene with file and console output."""
    # Create logs directory
    project_root = Path(__file__).parent.parent.parent
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Create logger
    logger = logging.getLogger("live_bci")
    logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # File handler with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"live_bci_{timestamp}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s.%(msecs)03d | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Console handler (less verbose)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(levelname)-8s | %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    logger.info(f"Live BCI log started: {log_file}")
    return logger


class LiveScene(BaseScene):
    """
    Scene for real-time BCI prediction and MQTT publishing.

    Reads EEG data from source, predicts direction using loaded ML model,
    and publishes results to MQTT broker for external device control.

    Follows MVC architecture:
    - Model: LiveModel - holds state and configuration
    - View: LiveView - handles rendering
    - Controller: LiveController - handles input and MQTT
    """

    def __init__(self, screen, clock, source=None):
        super().__init__(screen, clock)
        self.source = source
        
        # Setup logging
        self.log = setup_live_logger()
        self.log.info("=" * 60)
        self.log.info("LiveScene initialized")
        self.log.info("=" * 60)
        
        # MVC components
        self.model = LiveModel()
        self.view = LiveView(screen)
        self.controller = LiveController(self.model)
        
        # BCI processing state
        self.win_len = int(WIN_SEC * SAMPLE_RATE)
        self.hop = int(HOP_SEC * SAMPLE_RATE)
        self.chan_buf = np.zeros((0, N_CHANNELS))
        self.hist = deque(maxlen=MAJORITY_K)
        
        self.log.info(f"BCI Config: win_len={self.win_len}, hop={self.hop}, sample_rate={SAMPLE_RATE}")
        self.log.info(f"BCI Config: channels={N_CHANNELS}, conf_threshold={CONF_THRESHOLD}")
        
        # Async processing
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.bci_lock = threading.Lock()
        self.pending_result = None
        self.processing = False
        
        # Rate limiting for MQTT
        self.last_publish_time = 0.0
        self.last_direction = None
        
        # Update model with current state
        self._update_model_state()
        
        self.log.info(f"Model loaded: {model_store.has_model}")
        self.log.info(f"Source connected: {self.source is not None}")
    
    def _update_model_state(self):
        """Update model with current system state."""
        self.model.model_loaded = model_store.has_model
        self.model.source_connected = self.source is not None

    def run(self):
        """Main scene loop."""
        self.running = True
        
        try:
            while self.running:
                # Handle events
                for e in pg.event.get():
                    if e.type == pg.QUIT:
                        self._stop_session()
                        self.running = False
                    elif e.type == pg.KEYDOWN:
                        unicode_char = e.unicode if hasattr(e, 'unicode') else ""
                        action = self.controller.handle_keydown(e.key, unicode_char)
                        self._handle_action(action)
                
                # Process BCI if running
                if self.model.is_running:
                    self._process_bci()
                
                # Render
                self.view.render(self.model)
                pg.display.flip()
                self.clock.tick(60)
        
        finally:
            self._cleanup()
    
    def _handle_action(self, action: str):
        """Handle controller action."""
        if action == "quit":
            self._stop_session()
            self.running = False
        elif action == "start":
            self._start_session()
        elif action == "stop":
            self._stop_session()
        elif action == "connect":
            self.controller.connect_mqtt()
    
    def _start_session(self):
        """Start the live prediction session."""
        self.log.info("-" * 40)
        self.log.info("Starting live session...")
        
        if not model_store.has_model:
            self.log.error("Cannot start: No model loaded!")
            return
        
        self.log.info(f"Model info: {model_store.model_info}")
        
        # Connect to MQTT if not connected
        if not self.model.mqtt_connected:
            self.log.info(f"Connecting to MQTT: {self.model.mqtt_broker}:{self.model.mqtt_port}")
            self.controller.connect_mqtt()
            self.log.info(f"MQTT connected: {self.model.mqtt_connected}")
            if self.model.mqtt_error:
                self.log.error(f"MQTT error: {self.model.mqtt_error}")
        
        # Start EEG source
        if self.source:
            try:
                self.log.info("Starting EEG source...")
                self.source.start()
                self.log.info("EEG source started")
            except Exception as e:
                self.log.error(f"Error starting source: {e}")
        else:
            self.log.warning("No EEG source available!")
        
        # Reset state
        self.chan_buf = np.zeros((0, N_CHANNELS))
        self.hist.clear()
        self.last_publish_time = 0.0
        self.last_direction = None
        
        # Start session
        self.model.start_session()
        self.log.info("Session started - waiting for predictions...")
        self.log.info(f"MQTT topic: {self.model.mqtt_topic}")
        self.log.info(f"Confidence threshold: {self.model.confidence_threshold}")
        self.log.info(f"Publish interval: {self.model.publish_interval}s")
    
    def _stop_session(self):
        """Stop the live prediction session."""
        self.log.info("-" * 40)
        self.log.info("Stopping live session...")
        self.log.info(f"Session stats: predictions={self.model.predictions_count}, published={self.model.messages_published}")
        
        self.model.stop_session()
        
        # Stop EEG source
        if self.source:
            try:
                self.source.stop()
                self.log.info("EEG source stopped")
            except Exception as e:
                self.log.warning(f"Error stopping source: {e}")
    
    def _process_bci(self):
        """Process BCI data and publish predictions."""
        if not self.source or not model_store.has_model:
            return
        
        dt = self.clock.get_time() / 1000.0
        tnow = time.time()
        
        # Read samples
        n_need = max(1, int(dt * SAMPLE_RATE))
        try:
            samples = self.source.read(n_need)
            if samples is not None and len(samples) > 0:
                # Pad/trim channels if needed
                orig_shape = samples.shape
                if samples.shape[1] != N_CHANNELS:
                    samples = np.pad(
                        samples, ((0, 0), (0, max(0, N_CHANNELS - samples.shape[1])))
                    )[:, :N_CHANNELS]
                
                self.chan_buf = np.vstack([self.chan_buf, samples])
                
                # Log buffer status periodically
                if self.model.predictions_count % 10 == 0:
                    self.log.debug(f"Buffer: {self.chan_buf.shape[0]}/{self.win_len} samples, read {orig_shape}")
                
                # Limit buffer size
                if self.chan_buf.shape[0] > self.win_len * 3:
                    self.chan_buf = self.chan_buf[-self.win_len * 2:, :]
        except Exception as e:
            self.log.error(f"Error reading source: {e}")
            return
        
        # Check for pending results
        if self.pending_result and self.pending_result.done():
            try:
                result = self.pending_result.result()
                if result:
                    direction, confidence = result
                    
                    # Check if we should publish
                    time_since_last = tnow - self.last_publish_time
                    above_threshold = confidence >= self.model.confidence_threshold
                    time_ok = time_since_last >= self.model.publish_interval
                    
                    should_publish = above_threshold and time_ok
                    
                    self.log.debug(
                        f"Prediction: {direction} ({confidence:.2%}) | "
                        f"threshold={above_threshold}, time_ok={time_ok} ({time_since_last:.2f}s)"
                    )
                    
                    if should_publish:
                        published = self.controller.publish_direction(direction, confidence)
                        if published:
                            self.log.info(f"PUBLISHED: {direction} ({confidence:.2%}) → {self.model.mqtt_topic}")
                        else:
                            self.log.warning(f"PUBLISH FAILED: {direction} ({confidence:.2%})")
                        self.last_publish_time = tnow
                        self.last_direction = direction
                    else:
                        published = False
                        if not above_threshold:
                            self.log.debug(f"Not published: confidence {confidence:.2%} < {self.model.confidence_threshold:.2%}")
                    
                    self.model.add_prediction(direction, confidence, published)
                else:
                    self.log.debug("Prediction result was None")
            except Exception as e:
                self.log.error(f"Error getting prediction result: {e}")
                import traceback
                self.log.error(traceback.format_exc())
            
            self.pending_result = None
            self.processing = False
        
        # Submit new prediction task
        if self.chan_buf.shape[0] >= self.win_len and not self.processing:
            win = self.chan_buf[:self.win_len, :].copy()
            self.chan_buf = self.chan_buf[self.hop:, :]
            
            self.log.debug(f"Submitting prediction task, window shape: {win.shape}")
            self.pending_result = self.executor.submit(self._predict_async, win, tnow)
            self.processing = True
    
    def _predict_async(self, win, tnow):
        """
        Async prediction task.
        
        Args:
            win: EEG window (timesteps, channels)
            tnow: Current timestamp
            
        Returns:
            Tuple of (direction, confidence) or None
        """
        try:
            ml_model = model_store.model
            if ml_model is None:
                self.log.warning("No ML model in store!")
                return None
            
            # Flatten window for model
            X = win.flatten().reshape(1, -1)
            self.log.debug(f"Prediction input shape: {X.shape}, dtype: {X.dtype}")
            self.log.debug(f"Input stats: min={X.min():.4f}, max={X.max():.4f}, mean={X.mean():.4f}")
            
            # Predict
            predictions = ml_model.predict(X)
            pred_label = predictions[0]
            self.log.debug(f"Raw prediction: {pred_label} (type: {type(pred_label)})")
            
            # Map prediction to label
            label_map = {0: "backward", 1: "forward", 2: "left", 3: "right"}
            if isinstance(pred_label, (int, np.integer)):
                direction = label_map.get(int(pred_label), str(pred_label))
            else:
                direction = str(pred_label)
            
            self.log.debug(f"Mapped direction: {direction}")
            
            # Get confidence
            confidence = 0.8  # Default
            if hasattr(ml_model, 'predict_proba'):
                try:
                    proba = ml_model.predict_proba(X)[0]
                    confidence = float(np.max(proba))
                    self.log.debug(f"Prediction probabilities: {proba}")
                except Exception as e:
                    self.log.warning(f"Could not get predict_proba: {e}")
            
            self.log.debug(f"Final: direction={direction}, confidence={confidence:.2%}")
            
            # Apply majority voting
            with self.bci_lock:
                self.hist.append((direction, confidence))
                mv = majority_vote(list(self.hist), MAJORITY_K)
                
                if mv:
                    self.log.debug(f"Majority vote: {mv[0]} ({mv[1]:.2%})")
                    return mv  # (direction, confidence)
            
            return (direction, confidence)
            
        except Exception as e:
            self.log.error(f"Prediction error: {e}")
            import traceback
            self.log.error(traceback.format_exc())
            return None
    
    def _cleanup(self):
        """Clean up resources."""
        self._stop_session()
        self.controller.cleanup()
        self.executor.shutdown(wait=False)

