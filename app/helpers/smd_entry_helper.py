from typing import List, Dict

from app.db.smd_entry_store import client_exists, insert_smd_store_entry, update_smd_store_entry
from app.energy_agent.data_buffer import DataBuffer
from app.helpers.logs import log, logger


@log
async def process_data_buffer(data_buffer: DataBuffer, cid: str):
    """
    Process the data buffer, extract unique client_ids, store them in smd_store,
    and link them to the provided CID.
    :param data_buffer: List of dictionaries containing client_id and notarized data
    :param cid: The CID to be linked with all client_ids
    """
    unique_client_ids = set()
    for item in data_buffer.get_data():
        unique_client_ids.update(item.keys())
    for client_id in unique_client_ids:
        if not client_exists(client_id):
            insert_smd_store_entry(client_id, cid)
        else:
            update_smd_store_entry(client_id, cid)
    logger.debug(f"Processed {len(unique_client_ids)} unique client_ids from data buffer, linked to CID: {cid}")
