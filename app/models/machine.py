from pydantic import BaseModel, Field

from app.database.schema import DaoMachine


class MachineCreate(BaseModel):
    machine_id: str = Field(title="The public-key of a machine")
    machine_type: str = Field(title="The type of a machine", example="Machine Type 1")


class Machine(MachineCreate):
    id: int = Field(title="The unique identifier of a machine", example=1)

    @staticmethod
    def from_dao(dao: DaoMachine):
        return Machine(id=dao.id, machine_id=dao.machine_id, machine_type=dao.machine_type)
