from typing import Dict

from app.db.smd_entry_store import client_exists, insert_smd_store_entry, update_smd_store_entry
from app.helpers.logs import log, logger


@log
async def process_data_buffer(data_buffer: Dict, cid: str):
    """
    Process the data buffer, extract unique client_ids, store them in smd_store,
    and link them to the provided CID.
    :param data_buffer: List of dictionaries containing client_id and notarized data
    :param cid: The CID to be linked with all client_ids
    """
    client_ids = data_buffer.keys()
    for client_id in client_ids:
        if not client_exists(client_id):
            insert_smd_store_entry(client_id, cid)
        else:
            update_smd_store_entry(client_id, cid)
    logger.debug(f"Processed {client_ids} client_ids from data buffer, linked to CID: {cid}")
