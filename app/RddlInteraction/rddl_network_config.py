import os
from app.helpers.models import RDDLNetworkConfig


def get_rddl_network_settings(mode: str) -> RDDLNetworkConfig:
    network_config = RDDLNetworkConfig()
    lowercase_mode = mode.lower()
    if lowercase_mode == "mainnet":
        network_config.name = lowercase_mode
        network_config.chain_id = "planetmint-mainnet-1"
        network_config.planetmint_api = "https://api.rddl.io"
        network_config.explorer = "https://explorer.rddl.io"
        network_config.ta_base_url = "https://ta.rddl.io"
        network_config.mqtt.host = "mqtt.rddl.io"
        network_config.mqtt.port = 1884
        network_config.mqtt.password = "Xs0liJviALEJLWgHJ3vI4MbYHqahG0sP"
        network_config.mqtt.username = "rddl-tasmota"
    elif lowercase_mode == "testnet":
        network_config.name = lowercase_mode
        network_config.chain_id = "planetmint-testnet-1"
        network_config.planetmint_api = "https://testnet-api.rddl.io"
        network_config.explorer = "https://testnet-explorer.rddl.io"
        network_config.ta_base_url = "https://testnet-ta.rddl.io"
        network_config.mqtt.host = "testnet-mqtt.rddl.io"
        network_config.mqtt.port = 1886
        network_config.mqtt.password = "bE91dLR49FmsTtR2xbFCJfmgaGwTqeZJ"
        network_config.mqtt.username = "rddl-tasmota"
    elif lowercase_mode == "custom":
        network_config = setCustomRDDLConfig()
    else:
        network_config = setCustomRDDLConfig()
    return network_config


def setCustomRDDLConfig() -> RDDLNetworkConfig:
    network_config = RDDLNetworkConfig()
    network_config.name = "custom"
    network_config.chain_id = os.environ.get("CHAIN_ID") or "planetmintgo"
    network_config.planetmint_api = os.environ.get("PLANETMINT_API") or "http://localhost:1317"
    network_config.explorer = os.environ.get("PLANETMINT_EXPLORER") or "http://localhost:8000"
    network_config.ta_base_url = os.environ.get("TA_BASE_URL") or "http://localhost:8080"
    network_config.mqtt.host = os.environ.get("RDDL_MQTT_USER") or "user"
    network_config.mqtt.port = os.environ.get("RDDL_MQTT_PASSWORD") or "pwd"
    network_config.mqtt.password = os.environ.get("RDDL_MQTT_SERVER") or "localhost"
    network_config.mqtt.username = int(os.environ.get("RDDL_MQTT_PORT") or "1883")
    return network_config
