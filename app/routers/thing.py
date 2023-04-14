from typing import List

from fastapi import APIRouter

# from submodules.app_mypower_model.controller import thing as thing_controller
from app.dependencies import db_context
from app.schemas import Thing, ThingCreate

router = APIRouter(
    prefix="/things",
    tags=["things"],
    responses={404: {"detail": "Not found"}},
)


# @router.get("", response_model=List[Thing], summary="Return all things")
# async def get_things() -> List[Thing]:
#     """
#     Description
#     -----------
#     - Return all things.
#     """
#     with db_context() as db:
#         return await thing_controller.fetch_things(db)

#
# @router.get("/{thing_id}", response_model=Thing, summary="Return a thing by its public-key (thing_id)")
# async def get_thing_by_thing_id(thing_id: str) -> Thing:
#     """
#     Description
#     -----------
#     - Return a thing by its public-key (thing_id).
#     """
#     with db_context() as db:
#         return await thing_controller.fetch_thing_by_thing_id(db, thing_id)

#
# @router.post("", response_model=Thing, summary="Add a new thing")
# async def add_thing(thing: ThingCreate = None) -> Thing:
#     """
#     Description
#     -----------
#     - Add a new thing.
#     """
#     with db_context() as db:
#         return await thing_controller.save_thing(
#             db, thing.thing_id, thing.thing_type, thing.cid if thing.cid else None
#         )
