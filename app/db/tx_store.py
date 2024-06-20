import logging

from sqlite3 import Error
from app.db import execute_sql_command
from app.dependencies import config

logger = logging.getLogger(__name__)


def insert_tx(txhash, cid):
    execute_sql_command("INSERT INTO transactions (txhash, cid) VALUES (?, ?)", (txhash, cid))
    config.db_connection.commit()
    logger.debug("Transaction added.")


def get_cid(txhash):
    result = execute_sql_command("SELECT cid FROM transactions WHERE txhash=?", (txhash,), fetch_data=True)
    return result[0] if result else None


def update_cid(txhash, cid):
    execute_sql_command("UPDATE transactions SET cid = ? WHERE txhash = ?", (cid, txhash))
    config.db_connection.commit()
    logger.debug("Transaction updated.")


def delete_tx(txhash):
    execute_sql_command("DELETE FROM transactions WHERE txhash=?", (txhash,))
    config.db_connection.commit()
    logger.debug("Transaction deleted.")


def get_all_txhashes(order="DESC"):
    try:
        cursor = config.db_connection.cursor()
        cursor.execute(f"SELECT txhash, cid, created_at FROM transactions ORDER BY created_at {order}")
        result = cursor.fetchall()
        return result  # Returns a list of tuples where each tuple is (txhash, cid, created_at)
    except Error as e:
        logger.error(f"Failed to fetch all txhashes and cids: {e}")
