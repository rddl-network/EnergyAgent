from typing import Optional

from pydantic import BaseModel, Field


class MachineCreate(BaseModel):
    machine_id: str = Field(title="The public-key of the machine")
    machine_type: str = Field(title="The type of a machine", example="Machine Type 1")
    cid: Optional[str] = Field(title="The CID of the machine")


class Machine(MachineCreate):
    id: int = Field(title="The unique identifier of a machine", example=1)

    class Config:
        orm_mode = True
