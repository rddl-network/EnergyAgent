import json
from app.db import execute_sql_command

from app.helpers.logs import log, logger


@log
def transform_result(result):
    json_str = json.dumps(result[0]) if result else None
    if json_str:
        json_obj = json.loads(json_str)[0]
        return json.loads(json.loads(json_obj))
    else:
        return None


@log
def cid_exists(cid):
    result = execute_sql_command("SELECT cid FROM key_value_store WHERE cid=?", (cid,), fetch_data=True)
    if result is None or len(result) == 0:
        return False
    return True


@log
def insert_key_value(cid, json_value):
    if not cid_exists(cid):
        execute_sql_command(
            "INSERT INTO key_value_store (cid, json_value) VALUES (?, ?)", (cid, json.dumps(json_value))
        )
        logger.debug("Key-value pair added.")
    else:
        logger.debug("CID already exists. No action taken.")


@log
def get_value(cid) -> dict:
    result = execute_sql_command("SELECT json_value FROM key_value_store WHERE cid=?", (cid,), fetch_data=True)
    return transform_result(result)


@log
def delete_key(cid):
    execute_sql_command("DELETE FROM key_value_store WHERE cid=?", (cid,))
    logger.debug("Key-value pair deleted.")
