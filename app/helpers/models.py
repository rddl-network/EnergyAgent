from typing import List

from pydantic import BaseModel

LANDIS_GYR = "LANDIS_GYR"
SAGEMCOM = "SAGEMCOM"


class SmartMeterConfig(BaseModel):
    smart_meter_type: str = ""
    encryption_key: str = ""
    authentication_key: str = ""
    smart_meter_serial_port: str = "/dev/ttyUSB0"
    smart_meter_baudrate: int = 115200
    smart_meter_reading_interval: int = 900


class LandisGyrConfig(SmartMeterConfig):
    smart_meter_type: str = LANDIS_GYR
    address: int = 1
    smart_meter_baudrate: int = 2400


class SagemcomConfig(SmartMeterConfig):
    smart_meter_type: str = SAGEMCOM
    start_index: str = "5e4e"
    smart_meter_baudrate: int = 115200
    byte_size: int = 8
    parity: str = "N"
    stopbits: int = 1
    timeout: int = 90


class MQTTConfig(BaseModel):
    host: str = ""
    port: int = 0
    password: str = ""
    username: str = ""
    topic_prefix: str = ""


class AdditionalInfo(BaseModel):
    device_name: str = ""
    device_type: str = ""
    latitude: float = 0.0
    longitude: float = 0.0


class PlanetMintKeys(BaseModel):
    planetmint_address: str = ""
    extended_planetmint_pubkey: str = ""
    extended_liquid_pubkey: str = ""
    raw_planetmint_pubkey: str = ""


class OSCResponse(BaseModel):
    command: str = ""
    data: List[str] = []


class RDDLNetworkConfig(BaseModel):
    name: str = ""
    chain_id: str = ""
    planetmint_api: str = ""
    explorer: str = ""
    ta_base_url: str = ""
    mqtt: MQTTConfig = MQTTConfig()


class PoPContext(BaseModel):
    initiator: str = ""
    challenger: str = ""
    challengee: str = ""
    pop_height: int = 0
    isChallenger: bool = False
    isActive: bool = False
    cid: str = ""
