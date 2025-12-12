"""Model for LiveScene - holds state and data for live BCI to MQTT."""

from dataclasses import dataclass, field
from typing import Optional, List
from collections import deque
import time


@dataclass
class PredictionRecord:
    """Record of a single prediction."""
    timestamp: float
    direction: str
    confidence: float
    published: bool = False


class LiveModel:
    """Model for LiveScene - stores state and data without rendering logic."""

    def __init__(self):
        # MQTT Configuration
        self.mqtt_broker = "195.201.35.231"
        self.mqtt_port = 30183
        self.mqtt_topic = "car/control/"
        self.mqtt_connected = False
        self.mqtt_error: Optional[str] = None
        
        # BCI State
        self.is_running = False
        self.model_loaded = False
        self.source_connected = False
        
        # Prediction state
        self.current_direction: Optional[str] = None
        self.current_confidence: float = 0.0
        self.last_prediction_time: float = 0.0
        self.predictions_count = 0
        self.messages_published = 0
        
        # History for display
        self.prediction_history: deque = deque(maxlen=10)
        
        # Configuration
        self.confidence_threshold = 0.6
        self.publish_interval = 0.2  # Minimum seconds between publishes
        self.direction_labels = ["forward", "backward", "left", "right"]
        
        # Editable field tracking
        self.editing_field: Optional[str] = None  # "broker", "port", "topic", "threshold"
        self.edit_buffer = ""
        
        # Statistics
        self.session_start_time: Optional[float] = None
        self.direction_counts = {d: 0 for d in self.direction_labels}
    
    def start_session(self):
        """Start a new prediction session."""
        self.is_running = True
        self.session_start_time = time.time()
        self.predictions_count = 0
        self.messages_published = 0
        self.direction_counts = {d: 0 for d in self.direction_labels}
        self.prediction_history.clear()
    
    def stop_session(self):
        """Stop the prediction session."""
        self.is_running = False
    
    def add_prediction(self, direction: str, confidence: float, published: bool = False):
        """Record a new prediction."""
        now = time.time()
        self.current_direction = direction
        self.current_confidence = confidence
        self.last_prediction_time = now
        self.predictions_count += 1
        
        if direction in self.direction_counts:
            self.direction_counts[direction] += 1
        
        record = PredictionRecord(
            timestamp=now,
            direction=direction,
            confidence=confidence,
            published=published,
        )
        self.prediction_history.append(record)
        
        if published:
            self.messages_published += 1
    
    def get_session_duration(self) -> float:
        """Get session duration in seconds."""
        if self.session_start_time:
            return time.time() - self.session_start_time
        return 0.0
    
    def get_predictions_per_second(self) -> float:
        """Get prediction rate."""
        duration = self.get_session_duration()
        if duration > 0:
            return self.predictions_count / duration
        return 0.0
    
    def set_mqtt_connected(self, connected: bool, error: Optional[str] = None):
        """Update MQTT connection status."""
        self.mqtt_connected = connected
        self.mqtt_error = error
    
    def start_editing(self, field: str):
        """Start editing a configuration field."""
        self.editing_field = field
        if field == "broker":
            self.edit_buffer = self.mqtt_broker
        elif field == "port":
            self.edit_buffer = str(self.mqtt_port)
        elif field == "topic":
            self.edit_buffer = self.mqtt_topic
        elif field == "threshold":
            self.edit_buffer = str(self.confidence_threshold)
    
    def update_edit_buffer(self, char: str):
        """Add character to edit buffer."""
        self.edit_buffer += char
    
    def backspace_edit_buffer(self):
        """Remove last character from edit buffer."""
        if self.edit_buffer:
            self.edit_buffer = self.edit_buffer[:-1]
    
    def confirm_edit(self) -> bool:
        """Confirm the current edit."""
        if not self.editing_field:
            return False
        
        try:
            if self.editing_field == "broker":
                self.mqtt_broker = self.edit_buffer
            elif self.editing_field == "port":
                self.mqtt_port = int(self.edit_buffer)
            elif self.editing_field == "topic":
                self.mqtt_topic = self.edit_buffer
            elif self.editing_field == "threshold":
                val = float(self.edit_buffer)
                if 0 <= val <= 1:
                    self.confidence_threshold = val
                else:
                    return False
            self.editing_field = None
            self.edit_buffer = ""
            return True
        except ValueError:
            return False
    
    def cancel_edit(self):
        """Cancel current edit."""
        self.editing_field = None
        self.edit_buffer = ""

