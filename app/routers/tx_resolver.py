from typing import Dict, List

from fastapi import APIRouter

from app.db.tx_store import get_all_txhashes, insert_tx

router = APIRouter(
    prefix="/tx_resolver",
    tags=["tx"],
    responses={404: {"detail": "Not found"}},
)


@router.get("/txs")
async def resolve_tx() -> List[Dict]:
    transactions = get_all_txhashes()
    return [{"txhash": t[0], "cid": t[1], "created_at": t[2]} for t in transactions]


@router.post("")
async def resolve_tx(txhash: str, cid: str) -> dict:
    transactions = insert_tx(txhash, cid)
    return {"txhash": txhash, "cid": cid}
