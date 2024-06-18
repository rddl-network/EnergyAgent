import os
import logging
from sqlite3 import Error
from app.db import init_tables, create_connection


from app.helpers.config_helper import build_config_path
from app.RddlInteraction.TrustWallet.TrustWalletConnector import TrustWalletConnector
from app.RddlInteraction.rddl_network_config import get_rddl_network_settings

FILE_SMART_METER_CONFIG = "smart_meter_config.json"
FILE_MQTT_CONFIG = "mqtt_config.json"


class Config:
    def __init__(self):
        # general config
        self.log_level = os.environ.get("LOG_LEVEL") or "INFO"
        self.config_base_path = os.environ.get("CONFIG_PATH") or "/tmp"
        self.rddl_topic = os.environ.get("RDDL_TOPIC") or "rddl/SMD/#"
        self.path_to_smart_meter_config = build_config_path(self.config_base_path, FILE_SMART_METER_CONFIG)
        self.path_to_mqtt_config = build_config_path(self.config_base_path, FILE_MQTT_CONFIG)
        self.trust_wallet_port = os.environ.get("TRUST_WALLET_PORT") or "/dev/tty.usbmodem1101"
        self.notarize_interval = int(os.environ.get("NOTARIZE_INTERVAL") or 60)
        self.rddl_network_mode = os.environ.get("RDDL_NETWORK_MODE") or "testnet"
        self.rddl = get_rddl_network_settings(self.rddl_network_mode)

        # Database setup
        self.database = os.path.join(self.config_base_path, "energy_agent.db")
        try:
            self.db_connection = create_connection(self.database)
            try:
                init_tables(self.db_connection)
            except Error as e:
                logger.error(f"Failed to create tables: {e}")
        except Error as e:
            logger.error(f"Unable to connect to database: {e}")


config = Config()

numeric_level = getattr(logging, config.log_level.upper(), None)
if not isinstance(numeric_level, int):
    raise ValueError(f"Invalid log level: {config.log_level}")
logging.basicConfig(level=numeric_level)

logger = logging.getLogger(__name__)

trust_wallet_instance = TrustWalletConnector(config.trust_wallet_port)
