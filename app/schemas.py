from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class ThingCreate(BaseModel):
    thing_id: str = Field(title="The public-key of the thing")
    thing_type: str = Field(title="The type of a thing", example="Thing Type 1")
    cid: Optional[str] = Field(title="The CID of the thing")


class Thing(ThingCreate):
    id: int = Field(title="The unique identifier of a thing", example=1)

    class Config:
        orm_mode = True


class TimeSeriesDataCreate(BaseModel):
    created_at: datetime = Field(title="The timestamp of a time series data", example="2021-01-01 00:00:00")
    cid: Optional[str] = Field(title="The CID of the data")
    absolute_energy: Decimal = Field(title="The absolute value", example=1, decimal_places=5)
    unit: str = Field("kWh", description="The unit of energy", example="kWh")
    thing_id: int = Field(title="The thing id of a time series data", example=1)


class TimeSeriesData(TimeSeriesDataCreate):
    id: int = Field(title="The unique identifier of a time series data", example=1)

    class Config:
        orm_mode = True


class AggregatedTimeSeriesData(BaseModel):
    time_slot: datetime = Field(title="The time slot", example="2021-01-01 00:00:00")
    energy_value: Decimal = Field(title="The value energy for the requested interval", example=1)
    thing_id: int = Field(title="The thing id of a time series data", example=1)

    class Config:
        orm_mode = True
