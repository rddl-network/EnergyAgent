import json
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


def transform_result(result):
    return json.loads(result[0]) if result else None


def cid_exists(cid):
    result = execute_sql_command("SELECT cid FROM key_value_store WHERE cid=?", (cid,), fetch_data=True)
    return result is not None


def insert_key_value(cid, json_value):
    if not cid_exists(cid):
        execute_sql_command("INSERT INTO key_value_store (cid, json_value) VALUES (?, ?)",
                            (cid, json.dumps(json_value)))
        config.db_connection.commit()
        logger.debug("Key-value pair added.")
    else:
        logger.debug("CID already exists. No action taken.")


def get_value(cid):
    result = execute_sql_command("SELECT json_value FROM key_value_store WHERE cid=?", (cid,), fetch_data=True)
    return transform_result(result)


def delete_key(cid):
    execute_sql_command("DELETE FROM key_value_store WHERE cid=?", (cid,))
    config.db_connection.commit()
    logger.debug("Key-value pair deleted.")
