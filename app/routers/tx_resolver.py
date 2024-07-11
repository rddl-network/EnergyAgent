from typing import Dict, List, Optional

from fastapi import APIRouter
from pydantic import conint

from app.RddlInteraction.utils import table_pagination
from app.db.tx_store import get_all_txhashes

router = APIRouter(
    prefix="/tx_resolver",
    tags=["tx"],
    responses={404: {"detail": "Not found"}},
)


@router.get("/txs")
async def resolve_tx(
    page: Optional[conint(gt=0)] = None,
    page_size: Optional[conint(gt=0)] = None,
) -> List[Dict]:
    transactions = get_all_txhashes()
    tx_data = [{"txhash": t[0], "cid": t[1], "created_at": t[2]} for t in transactions]

    return table_pagination(page, page_size, tx_data)
