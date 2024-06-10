import logging
import os
import sqlite3

from app.helpers.config_helper import build_config_path
from app.RddlInteraction.TrustWallet.TrustWalletConnector import TrustWalletConnector

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
        self.machine_id = (
            os.environ.get("MACHINE_ID")
            or "0e9e54284f9b107d0ae1992709d2b1bc94885123d46f6b5353c0d6a7ef733bf38a995823947186fab58a4006f99f70a88210da2e6ebb56b0244e4120e02bfb61"
        )
        self.chain_id = os.environ.get("CHAIN_ID") or "planetmintgo"
        self.planetmint_api = os.environ.get("PLANETMINT_API") or "https://testnet-api.rddl.io"
        self.ta_base_url = os.environ.get("TA_BASE_URL") or "https://testnet-ta.rddl.io"
        self.rddl_mqtt_user = os.environ.get("RDDL_MQTT_USER") or "rddl-tasmota"
        self.rddl_mqtt_password = os.environ.get("RDDL_MQTT_PASSWORD") or "bE91dLR49FmsTtR2xbFCJfmgaGwTqeZJ"
        self.rddl_mqtt_server = os.environ.get("RDDL_MQTT_SERVER") or "testnet-mqtt.rddl.io"
        self.rddl_mqtt_port = os.environ.get("RDDL_MQTT_PORT") or "1886"

        # Database setup
        self.database = os.path.join(self.config_base_path, "energy_agent.db")
        self.db_connection = self.create_db_connection()
        self.init_tables()

    def create_db_connection(self):
        """Create a database connection to the SQLite database"""
        try:
            conn = sqlite3.connect(self.database)
            return conn
        except sqlite3.Error as e:
            logger.error(f"Unable to connect to database: {e}")
            return None

    def init_tables(self):
        """Initialize the tables if they do not exist"""
        if self.db_connection:
            try:
                cursor = self.db_connection.cursor()

                # SQL for creating key_value_store table
                create_key_value_store_table_sql = """
                CREATE TABLE IF NOT EXISTS key_value_store (
                    cid TEXT PRIMARY KEY,
                    json_value TEXT NOT NULL
                );
                """

                # SQL for creating transactions table
                create_transactions_table_sql = """
                CREATE TABLE IF NOT EXISTS transactions (
                    txhash TEXT NOT NULL,
                    cid TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """

                # Execute SQL statements
                cursor.execute(create_key_value_store_table_sql)
                cursor.execute(create_transactions_table_sql)

                # Commit the changes
                self.db_connection.commit()

            except sqlite3.Error as e:
                logger.error(f"Failed to create tables: {e}")


config = Config()

numeric_level = getattr(logging, config.log_level.upper(), None)
if not isinstance(numeric_level, int):
    raise ValueError(f"Invalid log level: {config.log_level}")
logging.basicConfig(level=numeric_level)

logger = logging.getLogger(__name__)

trust_wallet_instance = TrustWalletConnector(config.trust_wallet_port)
