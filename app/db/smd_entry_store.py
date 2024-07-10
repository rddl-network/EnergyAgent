import logging
from app.db import execute_sql_command
from app.dependencies import config
from typing import List, Optional

logger = logging.getLogger(__name__)


def client_exists(client_id: str) -> bool:
    """Check if a client_id exists in the smd_store table."""
    result = execute_sql_command("SELECT client_id FROM smd_store WHERE client_id=?", (client_id,), fetch_data=True)
    if result is None or len(result) == 0:
        return False
    return True


def insert_smd_store_entry(client_id: str, cid: str):
    """
    Insert a new entry into smd_store and link it with cids in smd_store_cid_link.
    """
    if not client_exists(client_id):
        execute_sql_command("INSERT INTO smd_store (client_id) VALUES (?)", (client_id,))
        existing = execute_sql_command(
            "SELECT 1 FROM smd_store_cid_link WHERE client_id=? AND cid=?", (client_id, cid), fetch_data=True
        )
        if not existing or len(existing) == 0:
            execute_sql_command("INSERT INTO smd_store_cid_link (client_id, cid) VALUES (?, ?)", (client_id, cid))
        logger.debug(f"SMD store entry added for client_id: {client_id}")
    else:
        logger.debug(f"Client ID {client_id} already exists. No action taken.")


def update_smd_store_entry(client_id: str, cid: str):
    """
    Add new cids linked to a client_id in smd_store_cid_link.
    If the link already exists, it will not be duplicated.
    """
    if client_exists(client_id):
        # Check if the link already exists
        existing = execute_sql_command(
            "SELECT 1 FROM smd_store_cid_link WHERE client_id=? AND cid=?", (client_id, cid), fetch_data=True
        )
        if not existing or len(existing) == 0:
            execute_sql_command("INSERT INTO smd_store_cid_link (client_id, cid) VALUES (?, ?)", (client_id, cid))
        logger.debug(f"SMD store entry updated for client_id: {client_id}")
    else:
        logger.debug(f"Client ID {client_id} does not exist. No action taken.")


def delete_smd_store_entry(client_id: str):
    """
    Delete an entry from smd_store and its associated links in smd_store_cid_link.
    """
    execute_sql_command("DELETE FROM smd_store_cid_link WHERE client_id=?", (client_id,))
    execute_sql_command("DELETE FROM smd_store WHERE client_id=?", (client_id,))
    logger.debug(f"SMD store entry deleted for client_id: {client_id}")


def get_all_client_ids() -> List[str]:
    """
    Retrieve all unique client_ids from the smd_store table.
    """
    query = "SELECT DISTINCT * FROM smd_store"
    results = execute_sql_command(query, params=(), fetch_data=True)

    # Assuming execute_sql_command returns a list of tuples
    return results if results else []


def get_smd_client_id_from_cid(cid: str) -> Optional[str]:
    """
    Retrieve the client_id associated with a specific CID.
    """
    result = execute_sql_command("SELECT client_id FROM smd_store_cid_link WHERE cid=?", (cid,), fetch_data=True)
    return result if result else None


def get_cids_for_client_id(client_id: str) -> List[str]:
    """
    Retrieve all CIDs associated with a specific client_id.
    """
    query = f"SELECT DISTINCT * FROM smd_store_cid_link WHERE client_id='{client_id}'"
    results = execute_sql_command(query, params=(), fetch_data=True)

    # Assuming execute_sql_command returns a list of tuples
    return results if results else []
