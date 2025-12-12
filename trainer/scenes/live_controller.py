"""Controller for LiveScene - handles input events and MQTT communication."""

import pygame as pg
from typing import Optional
import threading
import logging


class LiveController:
    """Controller for LiveScene - maps input to model updates and handles MQTT."""

    def __init__(self, model):
        self.model = model
        self.mqtt_client = None
        self._mqtt_lock = threading.Lock()
        self.log = logging.getLogger("live_bci")

    def handle_keydown(self, key, unicode_char: str = ""):
        """
        Handle keydown events and update model accordingly.

        Args:
            key: pygame key constant
            unicode_char: Unicode character for text input

        Returns:
            str: Action taken ('quit', 'start', 'stop', 'connect', 'none')
        """
        # Handle editing mode
        if self.model.editing_field:
            return self._handle_editing_key(key, unicode_char)
        
        # Handle running mode
        if self.model.is_running:
            return self._handle_running_key(key)
        
        # Handle config mode
        return self._handle_config_key(key)
    
    def _handle_editing_key(self, key, unicode_char: str):
        """Handle keys while editing a field."""
        if key == pg.K_ESCAPE:
            self.model.cancel_edit()
            return "none"
        elif key == pg.K_RETURN or key == pg.K_KP_ENTER:
            if self.model.confirm_edit():
                return "none"
            else:
                # Invalid input, flash error somehow
                return "none"
        elif key == pg.K_BACKSPACE:
            self.model.backspace_edit_buffer()
            return "none"
        elif unicode_char and unicode_char.isprintable():
            self.model.update_edit_buffer(unicode_char)
            return "none"
        return "none"
    
    def _handle_running_key(self, key):
        """Handle keys while session is running."""
        if key == pg.K_ESCAPE:
            return "quit"
        elif key == pg.K_SPACE:
            return "stop"
        return "none"
    
    def _handle_config_key(self, key):
        """Handle keys in configuration mode."""
        if key == pg.K_ESCAPE:
            return "quit"
        elif key == pg.K_1:
            self.model.start_editing("broker")
            return "none"
        elif key == pg.K_2:
            self.model.start_editing("port")
            return "none"
        elif key == pg.K_3:
            self.model.start_editing("topic")
            return "none"
        elif key == pg.K_4:
            self.model.start_editing("threshold")
            return "none"
        elif key == pg.K_c:
            return "connect"
        elif key == pg.K_RETURN or key == pg.K_KP_ENTER:
            if self.model.model_loaded and self.model.source_connected:
                return "start"
        return "none"

    def connect_mqtt(self) -> bool:
        """
        Connect to MQTT broker.
        
        Returns:
            True if connection successful
        """
        self.log.info(f"Attempting MQTT connection to {self.model.mqtt_broker}:{self.model.mqtt_port}")
        
        try:
            import paho.mqtt.client as mqtt
            self.log.debug(f"paho-mqtt version: {mqtt.__version__ if hasattr(mqtt, '__version__') else 'unknown'}")
            
            with self._mqtt_lock:
                # Disconnect existing client
                if self.mqtt_client:
                    self.log.debug("Disconnecting existing MQTT client")
                    try:
                        self.mqtt_client.disconnect()
                        self.mqtt_client.loop_stop()
                    except Exception as e:
                        self.log.debug(f"Error disconnecting old client: {e}")
                
                # Create new client
                self.log.debug("Creating new MQTT client")
                self.mqtt_client = mqtt.Client(
                    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                    client_id="cogniflow_bci",
                    protocol=mqtt.MQTTv5,
                )
                
                # Set callbacks
                self.mqtt_client.on_connect = self._on_connect
                self.mqtt_client.on_disconnect = self._on_disconnect
                
                # Connect
                self.log.info(f"Connecting to {self.model.mqtt_broker}:{self.model.mqtt_port}...")
                self.mqtt_client.connect(
                    self.model.mqtt_broker,
                    self.model.mqtt_port,
                    keepalive=60,
                )
                
                # Start network loop in background
                self.mqtt_client.loop_start()
                self.log.info("MQTT connection initiated, loop started")
                
                return True
                
        except ImportError as e:
            self.log.error(f"paho-mqtt not installed: {e}")
            self.model.set_mqtt_connected(False, "paho-mqtt not installed")
            return False
        except Exception as e:
            self.log.error(f"MQTT connection error: {e}")
            import traceback
            self.log.error(traceback.format_exc())
            self.model.set_mqtt_connected(False, str(e))
            return False
    
    def _on_connect(self, client, userdata, flags, reason_code, properties):
        """MQTT connection callback."""
        if reason_code == 0:
            self.model.set_mqtt_connected(True)
            self.log.info(f"✓ MQTT connected to {self.model.mqtt_broker}:{self.model.mqtt_port}")
        else:
            self.log.error(f"✗ MQTT connection failed: {reason_code}")
            self.model.set_mqtt_connected(False, f"Connection failed: {reason_code}")
    
    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        """MQTT disconnection callback."""
        self.log.warning(f"MQTT disconnected: {reason_code}")
        self.model.set_mqtt_connected(False, "Disconnected")

    def disconnect_mqtt(self):
        """Disconnect from MQTT broker."""
        with self._mqtt_lock:
            if self.mqtt_client:
                try:
                    self.mqtt_client.disconnect()
                    self.mqtt_client.loop_stop()
                except Exception:
                    pass
                self.mqtt_client = None
            self.model.set_mqtt_connected(False)

    def publish_direction(self, direction: str, confidence: float) -> bool:
        """
        Publish direction to MQTT base topic.
        
        Args:
            direction: Predicted direction (forward, backward, left, right)
            confidence: Prediction confidence (0-1)
            
        Returns:
            True if published successfully
        """
        self.log.debug(f"publish_direction called: direction={direction}, confidence={confidence:.2%}")
        self.log.debug(f"MQTT state: client={self.mqtt_client is not None}, connected={self.model.mqtt_connected}")
        
        if not self.mqtt_client:
            self.log.warning("Cannot publish: no MQTT client")
            return False
        
        if not self.model.mqtt_connected:
            self.log.warning("Cannot publish: MQTT not connected")
            return False
        
        try:
            # Publish direction as simple string to configured topic
            topic = self.model.mqtt_topic
            payload = direction
            
            self.log.debug(f"Publishing to topic: {topic}")
            self.log.debug(f"Payload: {payload}")
            
            result = self.mqtt_client.publish(
                topic,
                payload,
                qos=1,
            )
            
            self.log.debug(f"Publish result: rc={result.rc}, mid={result.mid}")
            
            success = result.rc == 0
            if success:
                self.log.info(f"✓ Published: {direction} ({confidence:.2%}) → {topic}")
            else:
                self.log.error(f"✗ Publish failed: rc={result.rc}")
            
            return success
            
        except Exception as e:
            self.log.error(f"MQTT publish error: {e}")
            import traceback
            self.log.error(traceback.format_exc())
            return False
    
    def cleanup(self):
        """Clean up resources."""
        self.log.info("Cleaning up LiveController...")
        self.disconnect_mqtt()
        self.log.info("LiveController cleanup complete")

