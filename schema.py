from datetime import datetime

from pydantic import BaseModel


class TimeSeries(BaseModel):
    timestamp: datetime
    value: float
