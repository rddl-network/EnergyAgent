import datetime
from pydantic import Field, BaseModel
from database.schema import DaoTimeSeriesData


class TimeSeriesDataCreate(BaseModel):
    timestamp: datetime = Field(title="The timestamp of a time series data", example="2021-01-01 00:00:00")
    kwh: float = Field(title="The kwh of a time series data", example=1.0)
    machine_id: int = Field(title="The machine id of a time series data", example=1)


class TimeSeriesData(BaseModel):
    id: int = Field(title="The unique identifier of a time series data", example=1)
    timestamp: datetime = Field(title="The timestamp of a time series data", example="2021-01-01 00:00:00")
    kwh: float = Field(title="The kwh of a time series data", example=1.0)
    machine_id: int = Field(title="The machine id of a time series data", example=1)

    @staticmethod
    def from_dao(dao: DaoTimeSeriesData):
        return TimeSeriesData(id=dao.id, timestamp=dao.timestamp, kwh=dao.kwh, machine_id=dao.machine_id)
