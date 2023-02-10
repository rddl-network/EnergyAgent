from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.machine import save_machine, fetch_machine_by_id, fetch_machines
from dependencies import get_db
from models.machine import MachineCreate, Machine

router = APIRouter(
    prefix="/machine",
    tags=["machine"],
    responses={404: {"detail": "Not found"}},
)


@router.get("/", response_model=List[Machine], summary="Return all machines")
def get_machines(db: Session = Depends(get_db)) -> List[Machine]:
    """
    Description
    -----------
    - Return all machines.
    """
    dao_machines = fetch_machines(db)
    return [Machine.from_dao(dao_machine) for dao_machine in dao_machines]


@router.get("/{machine_id}", response_model=Machine, summary="Return a machine by id")
def get_machine_by_id(db: Session = Depends(get_db), machine_id: int = 0) -> Machine:
    """
    Description
    -----------
    - Return a machine by id.
    """
    dao_machine = fetch_machine_by_id(db, machine_id)
    return Machine.from_dao(dao_machine)


@router.post("/", response_model=Machine, summary="Add a new machine")
def add_machine(
        db: Session = Depends(get_db),
        machine: MachineCreate = None,
) -> Machine:
    """
    Description
    -----------
    - Add a new machine.
    """
    dao_machine = save_machine(db, machine)
    return Machine.from_dao(dao_machine)
