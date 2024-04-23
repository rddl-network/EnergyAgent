from fastapi import APIRouter
from ipfs_cid import cid_sha256_hash

from app.db.cid_store import insert_key_value, get_value

router = APIRouter(
    prefix="/cid_resolver",
    tags=["cid"],
    responses={404: {"detail": "Not found"}},
)


@router.get("")
async def resolve_cid(cid: str) -> dict:
    data = get_value(cid)
    return {"cid": cid, "data": data}


@router.post("")
async def store_cid(data: str) -> dict:
    cid = cid_sha256_hash(data.encode("utf-8"))
    insert_key_value(cid, data)
    return {"cid": cid}
