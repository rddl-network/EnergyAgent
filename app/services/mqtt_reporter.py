import json
import paho.mqtt.client as mqtt
import time

from app.dependencies import (
    config,
    trust_wallet_instance,
    measurement_instance,
)
from app.helpers.config_helper import load_config
from app.helpers.models import MQTTConfig
from app.helpers.logs import logger


def publish_message(message: str):

    mqtt_config = MQTTConfig.model_validate(load_config(config.path_to_smart_meter_mqtt_config))
    # Create a MQTT client instance
    client = mqtt.Client()

    # Define callback functions
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT broker")
        else:
            print(f"Connection failed with code {rc}")

    def on_publish(client, userdata, mid):
        print(f"Message published successfully")

    # Set callbacks
    client.on_connect = on_connect
    client.on_publish = on_publish

    try:
        # Connect to the broker
        print("Connecting to broker...")
        if mqtt_config.username and mqtt_config.username != "":
            client.username_pw_set(mqtt_config.username, mqtt_config.password)  # Add this line before client.connect()

        client.connect(mqtt_config.host, mqtt_config.port, keepalive=60)

        # Start the loop to process network events
        client.loop_start()

        # Give some time for the connection to establish
        time.sleep(1)

        # Publish the message
        print(f"Publishing message to topic {mqtt_config.topic_prefix}")
        client.publish(mqtt_config.topic_prefix, message, qos=1)

        # Wait briefly for the message to be published
        time.sleep(2)

    finally:
        # Clean up
        print("Disconnecting...")
        client.loop_stop()
        client.disconnect()
        print("Disconnected from broker")


def broadcast_status():
    time.sleep(config.broadcast_delay)
    keys = trust_wallet_instance.get_planetmint_keys()
    state = measurement_instance.get_state(keys.planetmint_address, None)
    logger.debug(f"Report state: {state}")
    state_str = json.dumps(state)
    publish_message(state_str)
