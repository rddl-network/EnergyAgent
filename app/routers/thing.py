from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.controller import thing as thing_controller
from app.dependencies import get_db
from app.schemas import Thing, ThingCreate

router = APIRouter(
    prefix="/things",
    tags=["things"],
    responses={404: {"detail": "Not found"}},
)


@router.get("/", response_model=List[Thing], summary="Return all things")
async def get_things(db: Session = Depends(get_db)) -> List[Thing]:
    """
    Description
    -----------
    - Return all things.
    """
    return await thing_controller.fetch_things(db)


@router.get("/{thing_id}", response_model=Thing, summary="Return a thing by its public-key (thing_id)")
async def get_thing_by_thing_id(thing_id: str, db: Session = Depends(get_db)) -> Thing:
    """
    Description
    -----------
    - Return a thing by its public-key (thing_id).
    """
    return await thing_controller.fetch_thing_by_thing_id(db, thing_id)


@router.post("/", response_model=Thing, summary="Add a new thing")
async def add_thing(thing: ThingCreate = None, db: Session = Depends(get_db)) -> Thing:
    """
    Description
    -----------
    - Add a new thing.
    """
    return await thing_controller.save_thing(db, thing.thing_id, thing.thing_type, thing.cid if thing.cid else None)
