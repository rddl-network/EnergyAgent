from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.machine import (fetch_machine_by_id, fetch_machines,
                                  save_machine)
from app.dependencies import get_db
from app.models.machine import Machine, MachineCreate

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
    return fetch_machines(db)


@router.get("/{machine_id}", response_model=Machine, summary="Return a machine by id")
def get_machine_by_id(db: Session = Depends(get_db), machine_id: int = 0) -> Machine:
    """
    Description
    -----------
    - Return a machine by id.
    """
    dao_machine = fetch_machine_by_id(db, machine_id)
    if not dao_machine:
        raise HTTPException(status_code=404, detail='Machine not found.')
    return dao_machine


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
    return save_machine(db, machine)
