from dataclasses import dataclass


@dataclass(slots=True)
class SmartMeterConfig:
    def __init__(self):
        self.smart_meter_type: str
        self.encryption_key: str
        self.authentication_key: str
