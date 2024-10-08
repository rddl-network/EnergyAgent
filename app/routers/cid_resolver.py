from fastapi import APIRouter

from app.RddlInteraction.cid_tool import store_cid
from app.db.cid_store import get_value

router = APIRouter(
    prefix="/cid_resolver",
    tags=["cid"],
    responses={404: {"detail": "Not found"}},
)


@router.get("")
async def resolve_cid(cid: str) -> dict:
    data = get_value(cid)
    if not data:
        return {"cid": cid, "data": "Not found"}
    return {"cid": cid, "data": data}


@router.post("")
async def save_cid(data: str) -> dict:
    cid = store_cid(data)
    return {"cid": cid}
