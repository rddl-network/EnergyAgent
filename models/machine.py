from pydantic import Field, BaseModel

from database.schema import DaoMachine


class MachineCreate(BaseModel):
    name: str = Field(title="The name of a machine", example="Machine 1")
    type: str = Field(title="The type of a machine", example="Machine Type 1")


class Machine(BaseModel):
    id: int = Field(title="The unique identifier of a machine", example=1)
    name: str = Field(title="The name of a machine", example="Machine 1")
    type: str = Field(title="The type of a machine", example="Machine Type 1")

    @staticmethod
    def from_dao(dao: DaoMachine):
        return Machine(id=dao.id, name=dao.name, type=dao.type)
