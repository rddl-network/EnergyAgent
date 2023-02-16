from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.database.schema import DaoTimeSeriesData


class TimeSeriesDataCreate(BaseModel):
    timestamp: datetime = Field(title="The timestamp of a time series data", example="2021-01-01 00:00:00")
    cid: Optional[str] = Field(title="The CID of the data")
    absolute_energy: str = Field(title="The absolute value", example=1)
    unit: str = Field("kWh", description="The unit of energy", example="kWh")
    machine_id: int = Field(title="The machine id of a time series data", example=1)


class TimeSeriesData(TimeSeriesDataCreate):
    id: int = Field(title="The unique identifier of a time series data", example=1)

    @staticmethod
    def from_dao(dao: DaoTimeSeriesData):
        return TimeSeriesData(id=dao.id, timestamp=dao.timestamp, unit=dao.unit, absolute_energy=dao.absolute_energy, cid=dao.cid,
                              machine_id=dao.machine_id)
