import logging
import os
import sqlite3

from app.helpers.config_helper import build_config_path
from app.RddlInteraction.TrustWallet.occ_messages import TrustWalletInteraction

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
        self.notarize_interval = int(os.environ.get("NOTARIZE_INTERVAL") or 1)
        self.client_id = os.environ.get("CLIENT_ID") or "energy_agent"

        # Database setup
        self.database = os.path.join(self.config_base_path, "energy_agent.db")
        self.db_connection = self.create_db_connection()
        self.create_table()

    def create_db_connection(self):
        """Create a database connection to the SQLite database"""
        try:
            conn = sqlite3.connect(self.database)
            return conn
        except sqlite3.Error as e:
            logger.error(f"Unable to connect to database: {e}")
            return None

    def create_table(self):
        """Create the table if it does not exist"""
        if self.db_connection:
            try:
                cursor = self.db_connection.cursor()
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS key_value_store (
                        cid TEXT PRIMARY KEY,
                        json_value TEXT NOT NULL
                    )
                """
                )
                self.db_connection.commit()
            except sqlite3.Error as e:
                logger.error(f"Failed to create table: {e}")


config = Config()

numeric_level = getattr(logging, config.log_level.upper(), None)
if not isinstance(numeric_level, int):
    raise ValueError(f"Invalid log level: {config.log_level}")
logging.basicConfig(level=numeric_level)

logger = logging.getLogger(__name__)

trust_wallet_instance = TrustWalletInteraction(config.trust_wallet_port)

