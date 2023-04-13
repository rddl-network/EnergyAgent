from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(slots=True)
class MeterData:
    device_type: str
    energy_consumed: float
    energy_delivered: float
    positive_reactive_energy: float
    negative_reactive_energy: float
    active_power_consumption: int
    active_power_delivery: int
    positive_reactive_power: Optional[int] = None
    negative_reactive_power: Optional[int] = None
    timestamp: Optional[datetime] = None
