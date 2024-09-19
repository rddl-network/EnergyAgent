import json
import requests
from sqlite3 import Error
from app.db import execute_sql_command
from app.dependencies import config

from app.helpers.logs import log, logger

MQTT_ACTIVITY = "mqtt"
TX_ACTIVITY = "tx"


@log
def insert_mqtt_activity(command, result, context):
    context_str = convert_context_to_str(context)
    execute_sql_command(
        "INSERT INTO activities (type, txhash, command, result, context)\
        VALUES (?, ?, ?, ?, ?)",
        (MQTT_ACTIVITY, "", command, result, context_str),
    )
    logger.debug("Activity added: MQTT.")


@log
def insert_tx_activity(tx, result, context):
    context_str = convert_context_to_str(context)
    execute_sql_command(
        "INSERT INTO activities (type, txhash, command, result, context)\
        VALUES (?, ?, ?, ?, ?)",
        (TX_ACTIVITY, tx, "", result, context_str),
    )
    logger.debug("Activity added: TX.")


@log
def convert_context_to_str(context):
    if isinstance(context, dict):
        return json.dumps(context)
    elif isinstance(context, str):
        return context
    else:
        return str(context)


@log
def insert_tx_activity_by_response(response: requests.Response, context):
    tx_hash = ""
    msg = response.reason + " " + response.text
    if response.status_code == 200:
        tx_hash = json.loads(response.text)["tx_response"]["txhash"]
        msg = response.text

    insert_tx_activity(tx_hash, msg, context)


@log
def get_all_activities(order="DESC"):
    try:
        cursor = config.db_connection.cursor()
        cursor.execute(
            f"SELECT type, txhash, command, result, context, timestamp FROM activities ORDER by id {order}"
        )
        result = cursor.fetchall()
        return result  # Returns a list of tuples where each tuple is (type, txhash, command, result, context )
    except Error as e:
        logger.error(f"Failed to fetch all activities: {e}")
        return None
