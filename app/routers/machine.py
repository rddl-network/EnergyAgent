from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.controller import machine as machine_controller
from app.dependencies import get_db
from app.schemas import Machine, MachineCreate

router = APIRouter(
    prefix="/machine",
    tags=["machine"],
    responses={404: {"detail": "Not found"}},
)


@router.get("/", response_model=List[Machine], summary="Return all machines")
async def get_machines(db: Session = Depends(get_db)) -> List[Machine]:
    """
    Description
    -----------
    - Return all machines.
    """
    return await machine_controller.fetch_machines(db)


@router.get("/{machine_id}", response_model=Machine, summary="Return a machine by its public-key (machine_id)")
async def get_machine_by_machine_id(machine_id: str, db: Session = Depends(get_db)) -> Machine:
    """
    Description
    -----------
    - Return a machine by its public-key (machine_id).
    """
    return await machine_controller.fetch_machine_by_machine_id(db, machine_id)


@router.post("/", response_model=Machine, summary="Add a new machine")
async def add_machine(machine: MachineCreate = None, db: Session = Depends(get_db)) -> Machine:
    """
    Description
    -----------
    - Add a new machine.
    """
    return await machine_controller.save_machine(db, machine.machine_id, machine.machine_type,
                                                 machine.cid if machine.cid else None)
