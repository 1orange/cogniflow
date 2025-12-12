import paho.mqtt.client as mqtt
import time

# MQTT settings
BROKER = "195.201.35.231"   # my mqtt
PORT = 30183
TOPIC = "car/control/"
MESSAGE = "Hello from Python MQTT!"

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
