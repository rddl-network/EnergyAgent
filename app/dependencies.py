import os
from app.db import init_tables, create_connection
from app.energy_agent.data_buffer import DataBuffer

from app.helpers.config_helper import build_config_path
from app.RddlInteraction.TrustWallet.TrustWalletConnector import TrustWalletConnector
from app.RddlInteraction.rddl_network_config import get_rddl_network_settings
from app.helpers.logs import log, setup_logging
from app.model.measurements import Measurements

FILE_SMART_METER_CONFIG = "smart_meter_config.json"
FILE_MQTT_CONFIG = "mqtt_config.json"
FILE_SMART_METER_MQTT_CONFIG = "smart_meter_mqtt_config.json"
METADATA_CONFIG_PATH = "smart_meter_metadata.json"


PRODUCTION_READOUT_MODE_SMARTFOX = "SMARTFOX"
PRODUCTION_READOUT_MODE_CERBOGX = "CERBOGX"
PRODUCTION_READOUT_MODE_SHELLYPRO3EM = "SHELLYPRO3EM"


@log
class Config:
    def __init__(self):
        # general config
        self.config_base_path = os.environ.get("CONFIG_PATH") or "/tmp"
        self.smd_topic = os.environ.get("SMD_TOPIC") or "rddl/SMD/#"
        self.path_to_mqtt_config = build_config_path(self.config_base_path, FILE_MQTT_CONFIG)
        self.path_to_smart_meter_config = build_config_path(self.config_base_path, FILE_SMART_METER_CONFIG)
        self.path_to_smart_meter_mqtt_config = build_config_path(self.config_base_path, FILE_SMART_METER_MQTT_CONFIG)
        self.metadata_config_path = build_config_path(self.config_base_path, METADATA_CONFIG_PATH)
        self.trust_wallet_port = os.environ.get("TRUST_WALLET_PORT") or "/dev/ttyACM0"
        self.notarize_interval = int(os.environ.get("NOTARIZE_INTERVAL") or 60)
        self.rddl_network_mode = os.environ.get("RDDL_NETWORK_MODE") or "mainnet"
        self.rddl = get_rddl_network_settings(self.rddl_network_mode)
        self.production_readout_mode = os.environ.get("PRODUCTION_READOUT_MODE") or ""
        self.production_readout_ip = os.environ.get("PRODUCTION_READOUT_IP") or ""
        self.production_readout_pattern = (
            os.environ.get("PRODUCTION_READOUT_PATTERN") or "^N/[^/]+/pvinverter/[^/]+/Ac/Energy/Forward$"
        )  # this is used for mqtt topic parsing

        # logging config
        self.log_level = os.environ.get("LOG_LEVEL") or "INFO"
        self.json_logs = os.environ.get("JSON_LOGS") or "0"
        self.log_file_path = os.environ.get("LOG_FILE_PATH") or "/tmp/log/energy-agent.log"
        self.log_rotation_size = os.environ.get("LOG_ROTATION_SIZE") or "100 MB"
        self.log_retention = os.environ.get("LOG_RETENTION") or "1 month"
        self.disable_third_party_log = os.environ.get("DISABLE_THIRD_PARTY_LOG") or "0"

        # Database setup
        self.database = os.path.join(self.config_base_path, "energy_agent.db")
        self.db_connection = create_connection(self.database)
        init_tables(self.db_connection)


config = Config()
setup_logging(
    log_level=config.log_level,
    json_logs=config.json_logs,
    log_rotation_size=config.log_rotation_size,
    log_retention=config.log_retention,
    disable_third_party_log=config.disable_third_party_log,
    log_file_path=config.log_file_path,
)

trust_wallet_instance = TrustWalletConnector(port_name=config.trust_wallet_port, timeout=600000)
data_buffer = DataBuffer()
measurement_instance = Measurements()
