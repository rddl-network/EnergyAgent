import json
from datetime import datetime
import asyncio
import random

from gmqtt import Client as MQTTClient
from gmqtt import Message
from gmqtt.mqtt.constants import MQTTv311

import app.RddlInteraction.api_queries
from app.dependencies import config, logger
from app.helpers.models import MQTTConfig
from app.dependencies import trust_wallet_instance
from app.db.cid_store import get_value
from app.RddlInteraction.cid_tool import compute_cid


from app.RddlInteraction.planetmint_interaction import (
    getPoPResultTx,
    broadcastTX,
    getAccountInfo,
)


class RDDLAgent:
    def __init__(self):
        logger.info(f"MQTT RDDL creation")
        self.client = None
        self.mqtt_config = MQTTConfig()
        self.stopped = False
        self.data_buffer = []
        self.max_buffer_size = 3000
        self.retry_attempts = 3
        self.mqtt_config.mqtt_username = config.rddl_mqtt_user
        self.mqtt_config.mqtt_password = config.rddl_mqtt_password
        self.mqtt_config.mqtt_host = config.rddl_mqtt_server
        self.mqtt_config.mqtt_port = config.rddl_mqtt_port
        self.clear_pop_context()

    def setup(self):
        try:
            logger.info(f"MQTT RDDL setup")
            keys = trust_wallet_instance.get_planetmint_keys()
            self.client = MQTTClient(client_id=keys.planetmint_address)
            self.client.on_message = self.on_message
            self.client.set_auth_credentials(self.mqtt_config.mqtt_username, self.mqtt_config.mqtt_password)
        except Exception as e:
            logger.error(f"MQTT RDDL Setup error: {e}")
            raise

    async def connect_to_mqtt(self):
        try:
            logger.info(f"MQTT RDDL connect")
            await self.client.connect(
                self.mqtt_config.mqtt_host, self.mqtt_config.mqtt_port, keepalive=60, version=MQTTv311, ssl=True
            )
        except Exception as e:
            logger.error(f"MQTT RDDL connection error: {e}")
            raise

    async def disconnect_from_mqtt(self):
        try:
            logger.info(f"MQTT RDDL disconnection")
            await self.client.disconnect()
        except Exception as e:
            logger.error(f"MQTT RDDL disconnection error: {e}")

    async def on_message(self, client, topic, payload, qos, properties):
        try:
            decoded_payload = payload.decode()
            logger.info(f"MQTT RDDL Received message: {topic}, {decoded_payload}")
            keys = trust_wallet_instance.get_planetmint_keys()
            if topic == "cmnd/" + keys.planetmint_address + "/PoPChallenge":
                asyncio.create_task(self.pop_challenge(decoded_payload))
            elif topic == "cmnd/" + keys.planetmint_address + "/PoPInit":
                asyncio.create_task(self.pop_init(decoded_payload))
            elif self.challengee != "" and topic == "cmnd/" + self.challengee + "/PoPChallengeResult":
                asyncio.create_task(self.pop_challenge_result(decoded_payload))
            else:
                logger.debug(f"MQTT RDDL topic currently not supported: " + topic)
        except UnicodeDecodeError:
            logger.error("MQTT RDDL Error decoding the message payload")
        except Exception as e:
            logger.error(f"MQTT RDDL Unexpected error processing message: {e}")

    def clear_pop_context(self):
        self.challengee = ""
        self.challenger = ""
        self.cid = ""
        self.initiator = ""
        self.pop_height = 0

    async def pop_init(self, data):
        logger.info("PoP init: " + data)
        (initiator, challenger, challengee, pop_height, isChallenger, valid) = await app.RddlInteraction.api_queries.queryPoPInfo(data)
        logger.info("challenger : " + challenger)
        logger.info("challengee : " + challengee)
        logger.info("valid : " + str(valid))
        if valid:
            self.initiator = initiator
            self.challenger = challenger
            self.challengee = challengee
            self.pop_height = pop_height
            if isChallenger:
                asyncio.create_task(self.initPoPChallenge(challengee))
                return
            else:
                # wait for PoP challenge
                return

    async def pop_challenge(self, data: str):
        logger.info("PoP challenge : " + data)
        if self.challengee != trust_wallet_instance.get_planetmint_keys().planetmint_address:
            return
        cid = data
        cid_data = get_value(cid)
        cid_data_hex = app.RddlInteraction.utils.toHexString(cid_data)
        topic = "cmnd/" + self.challengee + "/PoPChallengeResult"
        payload = (
            '{ "PoPChallengeResult": { "cid": "' + cid + '", "encoding": "hex", "data": "' + cid_data_hex + '"} }'
        )
        msg = Message(
            topic,
            payload,
            qos=1,
            content_type="json",
            message_expiry_interval=60,
            user_property=("time", str(datetime.now())),
        )
        self.client.publish(msg)
        self.clear_pop_participants()
        return

    async def sendPoPResult(self, success: bool):
        keys = trust_wallet_instance.get_planetmint_keys()
        accountID, sequence, status = getAccountInfo(config.planetmint_api, keys.planetmint_address)
        if status != "":
            logger.error(f"error: {status}, message: {status}")
        txMsg = getPoPResultTx(
            self.challengee, self.initiator, self.pop_height, success, config.chain_id, accountID, sequence
        )
        response = broadcastTX(txMsg)
        if response.status_code != 200:
            logger.error(f"error: {response.reason,}, message: {response.text}")

    async def pop_challenge_result(self, data):
        logger.info("PoP challenge result: " + data)
        self.client.unsubscribe("stat/" + self.challengee + "/PoPChallengeResult")
        try:
            jsonObj = json.loads(data)
            jsonObj["PoPChallengeResult"]["data"]
            if self.cid != jsonObj["PoPChallengeResult"]["cid"]:
                logger.error(
                    "RDDL MQTT PoP Result: wrong cid. expected "
                    + self.cid
                    + " got "
                    + jsonObj["PoPChallengeResult"]["cid"]
                )
                asyncio.create_task(self.sendPoPResult(False))
            elif "hex" != jsonObj["PoPChallengeResult"]["encoding"]:
                logger.error("RDDL MQTT PoP Result: unsupported encoding.")
                asyncio.create_task(self.sendPoPResult(False))
            else:
                cid_data_encoded = jsonObj["PoPChallengeResult"]["data"]
                cid_data = app.RddlInteraction.utils.fromHexString(cid_data_encoded)
                computed_cid = compute_cid(cid_data)
                if computed_cid == self.cid:
                    asyncio.create_task(self.sendPoPResult(True))
                else:
                    asyncio.create_task(self.sendPoPResult(False))
        except json.JSONDecodeError:
            logger.error("RDDL MQTT PoP Result: Error: Invalid JSON string.")
            asyncio.create_task(self.sendPoPResult(False))

    async def initPoPChallenge(self, challengee: str):
        logger.info("RDDL MQTT init PoP")
        cids = await app.RddlInteraction.api_queries.queryNotatizedAssets(challengee, 20)
        if not cids or len(cids) == 0:
            logger.error("RDDL MQTT init PoP could not retriev cids.")
            asyncio.create_task(self.sendPoPResult(False))
            return

        random_cid = random.choice(cids)
        self.cid = random_cid
        self.client.subscribe("cmnd/" + challengee + "/PoPChallengeResult")
        topic = "cmnd/" + challengee + "/PoPChallenge"
        msg = Message(
            topic,
            random_cid,
            qos=1,
            content_type="raw",
            message_expiry_interval=60,
            user_property=("time", str(datetime.now())),
        )
        self.client.publish(msg)
        return

    async def run(self):
        logger.info("RDDL MQTT run.")
        try:
            await self.connect_to_mqtt()
            keys = trust_wallet_instance.get_planetmint_keys()

            self.client.subscribe("cmnd/" + keys.planetmint_address + "/PoPChallenge")
            self.client.subscribe("cmnd/" + keys.planetmint_address + "/PoPInit")

            self.client.subscribe(config.rddl_topic)

            while not self.stopped:
                logger.info("RDDL MQTT enter wait loop.")
                asyncio.create_task( self.postStatus(keys.planetmint_address) )
                await asyncio.sleep(60)

        except Exception as e:
            logger.error(f"MQTT RDDL Error in RDDLAgent run loop: {e}")
        finally:
            logger.info("RDDL MQTT stop run.")
            await self.disconnect_from_mqtt()

    async def postStatus(self, address: str):
        logger.info("RDDL MQTT publish status.")
        topic = "tele/" + address + "/STATE"
        payload = '{"Time": "' + str(datetime.now()) + '" }'
        msg = Message(
            topic,
            payload,
            qos=1,
            content_type="json",
            message_expiry_interval=300,
            user_property=("time", str(datetime.now())),
        )
        self.client.publish(msg)
