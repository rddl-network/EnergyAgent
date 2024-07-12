from typing import Optional
from fastapi import APIRouter
from pydantic import conint

from app.RddlInteraction.utils import table_pagination
from app.db.smd_entry_store import (
    get_all_client_ids,
    insert_smd_store_entry,
    delete_smd_store_entry,
    get_smd_client_id_from_cid,
    get_cids_for_client_id,
    client_exists,
    update_smd_store_entry,
)

router = APIRouter(
    prefix="/smd-entry",
    tags=["smd-entry"],
    responses={404: {"detail": "Not found"}},
)


@router.get("")
async def get_smd_entries(
    page: Optional[conint(gt=0)] = None,
    page_size: Optional[conint(gt=0)] = None,
):
    results = get_all_client_ids()
    smd_entries = [t[0] for t in results]
    return table_pagination(page, page_size, smd_entries)


@router.post("")
async def add_smd_entry(client_id: str, cid: str):
    if client_exists(client_id):
        update_smd_store_entry(client_id, cid)
    else:
        insert_smd_store_entry(client_id, cid)


@router.delete("")
async def update_smd_entry(client_id: str):
    delete_smd_store_entry(client_id)


@router.get("/cids/{client_id}")
async def get_cids_for_smd(
    client_id: str,
    page: Optional[conint(gt=0)] = None,
    page_size: Optional[conint(gt=0)] = None,
):
    results = get_cids_for_client_id(client_id)
    cids = [t[1] for t in results]
    return table_pagination(page, page_size, cids)


@router.get("/cid/{cid}")
async def get_smd_for_cid(cid: str):
    results = get_smd_client_id_from_cid(cid)
    return results
