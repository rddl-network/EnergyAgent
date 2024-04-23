from pydantic import BaseModel


class SmartMeterConfig(BaseModel):
    smart_meter_type: str = ""
    encryption_key: str = ""
    authentication_key: str = ""
    smart_meter_topic: str = ""


class TopicConfig(BaseModel):
    topics: list[str]


class AdditionalInfo(BaseModel):
    device_name: str = ""
    device_type: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
