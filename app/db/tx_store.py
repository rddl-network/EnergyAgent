import logging
import sqlite3
from app.dependencies import config

logger = logging.getLogger(__name__)


def execute_sql_command(sql_command, params, fetch_data=False):
    try:
        cursor = config.db_connection.cursor()
        cursor.execute(sql_command, params)
        if fetch_data:
            return cursor.fetchone()
    except sqlite3.Error as e:
        logger.error(f"Failed to carry out SQL command: {e}")


def insert_tx(txhash, cid):
    execute_sql_command(
        "INSERT INTO transactions (txhash, cid) VALUES (?, ?, CURRENT_TIMESTAMP)", (txhash, cid)
    )
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


def get_all_txhashes():
    try:
        cursor = config.db_connection.cursor()
        cursor.execute("SELECT txhash, cid, created_at FROM transactions")
        result = cursor.fetchall()
        return result  # Returns a list of tuples where each tuple is (txhash, cid, created_at)
    except sqlite3.Error as e:
        logger.error(f"Failed to fetch all txhashes and cids: {e}")
