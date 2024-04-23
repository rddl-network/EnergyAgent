import logging
import os
import sqlite3

from app.helpers.config_helper import build_config_path

FILE_SMART_METER_CONFIG = "smart_meter_config.json"
FILE_TOPIC_CONFIG = "topic_config.json"
FILE_ADD_INFO = "additional_info.json"


class Config:
    def __init__(self):
        # general config
        self.log_level = os.environ.get("LOG_LEVEL") or "INFO"
        self.pubkey = os.environ.get("PUBKEY") or "st-energy-meter"
        self.config_base_path = os.environ.get("CONFIG_PATH") or "/tmp"
        self.path_to_topic_config = build_config_path(self.config_base_path, FILE_TOPIC_CONFIG)
        self.path_to_smart_meter_config = build_config_path(self.config_base_path, FILE_SMART_METER_CONFIG)

        # Data MQTT Config
        self.data_mqtt_host = os.environ.get("MQTT_HOST") or "mqtt"
        self.data_mqtt_port: int = int(os.environ.get("MQTT_PORT") or 1893)
        self.data_mqtt_password = os.environ.get("MQTT_PASSWORD") or ""
        self.data_mqtt_username = os.environ.get("MQTT_USERNAME") or ""
        self.data_mqtt_topic = os.environ.get("MQTT_TOPIC") or ""

        # Smart Meter Config
        self.device = os.environ.get("DEVICE") or "WN"
        self.encryption_key = os.environ.get("ENCRYPTION_KEY") or None
        self.authentication_key = os.environ.get("AUTH_KEY") or None
        self.path_smart_meter_config = os.environ.get("PATH_SMART_METER_CONFIG") or "smart_meter_config.json"

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
