from fastapi import APIRouter

from app.db.tx_store import get_all_txhashes

router = APIRouter(
    prefix="/tx_resolver",
    tags=["tx"],
    responses={404: {"detail": "Not found"}},
)


@router.get("")
async def resolve_tx() -> dict:
    transactions = get_all_txhashes()
    return transactions
