from typing import List

from pydantic import BaseModel


class SmartMeterConfig(BaseModel):
    smart_meter_type: str = ""
    encryption_key: str = ""
    authentication_key: str = ""
    smart_meter_topic: str = ""


class TopicConfig(BaseModel):
    topics: list[str] = []

    def contains(self, topic: str) -> bool:
        return topic in self.topics


class MQTTConfig(BaseModel):
    host: str = ""
    port: int = 0
    password: str = ""
    username: str = ""


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
    chain_id: str = ""
    planetmint_api: str = ""
    ta_base_url: str = ""
    mqtt: MQTTConfig = MQTTConfig()
