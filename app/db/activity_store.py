import logging
import json
import requests
from sqlite3 import Error
from app.db import execute_sql_command
from app.dependencies import config

logger = logging.getLogger(__name__)

MQTT_ACTIVITY = "mqtt"
TX_ACTIVITY = "tx"


def insert_mqtt_activity(command, result, context):
    execute_sql_command(
        "INSERT INTO activities (type, txhash, command, result, context)\
        VALUES (?, ?, ?, ?, ?)",
        (MQTT_ACTIVITY, "", command, result, context),
    )
    config.db_connection.commit()
    logger.debug("Activity added: MQTT.")


def insert_tx_activity(tx, result, context):
    execute_sql_command(
        "INSERT INTO activities (type, txhash, command, result, context)\
        VALUES (?, ?, ?, ?, ?)",
        (TX_ACTIVITY, tx, "", result, context),
    )
    config.db_connection.commit()
    logger.debug("Activity added: TX.")


def insert_tx_activity_by_response(response: requests.Response, context):
    tx_hash = ""
    msg = response.reason + " " + response.text
    if response.status_code == 200:
        tx_hash = json.loads(response.text)["tx_response"]["txhash"]
        msg = response.text

    insert_tx_activity(tx_hash, msg, context)


def get_all_activities():
    try:
        cursor = config.db_connection.cursor()
        cursor.execute(
            "SELECT type, txhash, command, result, context, timestamp FROM activities ORDER by timestamp DESC"
        )
        result = cursor.fetchall()
        return result  # Returns a list of tuples where each tuple is (type, txhash, command, result, context )
    except Error as e:
        logger.error(f"Failed to fetch all activities: {e}")
        return None
