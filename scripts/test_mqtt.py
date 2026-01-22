"""Test script for MQTT publishing - simulates Live BCI output."""
import paho.mqtt.client as mqtt
import time

# MQTT settings (should match Live scene defaults in live_model.py)
BROKER = "195.201.35.231"
PORT = 30183
TOPIC = "car/control/"
MESSAGE = "forward"  # Simulates a direction prediction

# Callback when connected
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker")
    else:
        print(f"Connection failed with code {rc}")

# Create MQTT client
client = mqtt.Client()
client.on_connect = on_connect

# Connect to broker
client.connect(BROKER, PORT, keepalive=60)

# Start network loop
client.loop_start()

# Give time to connect
time.sleep(1)

# Publish message
client.publish(TOPIC, MESSAGE)
print(f"Message sent to topic '{TOPIC}'")

# Clean up
time.sleep(1)
client.loop_stop()
client.disconnect()
