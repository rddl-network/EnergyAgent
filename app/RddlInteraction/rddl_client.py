import json
from datetime import datetime
import asyncio
import random

from gmqtt import Client as MQTTClient
from gmqtt import Message
from gmqtt.mqtt.constants import MQTTv311

from app.dependencies import config, logger, trust_wallet_instance
from app.db.cid_store import get_value
from app.RddlInteraction import utils
from app.RddlInteraction.cid_tool import compute_cid
from app.RddlInteraction.api_queries import queryPoPInfo, getAccountInfo, queryNotatizedAssets
from app.RddlInteraction.planetmint_interaction import broadcastTX, getPoPResultTx


class RDDLAgent:
    def __init__(self):
        logger.info(f"MQTT RDDL creation")

        # client management
        self.client = None
        self.stopped = False
        self.data_buffer = []
        self.max_buffer_size = 3000
        self.retry_attempts = 3

        # network management
        self.clear_pop_context()

    def setup(self):
        try:
            logger.info(f"MQTT RDDL setup")
            keys = trust_wallet_instance.get_planetmint_keys()
            self.client = MQTTClient(client_id=keys.planetmint_address)
            self.client.on_message = self.on_message
            self.client.set_auth_credentials(config.rddl.mqtt.username, config.rddl.mqtt.password)
        except Exception as e:
            logger.error(f"MQTT RDDL Setup error: {e}")
            raise

    async def connect_to_mqtt(self):
        try:
            logger.info(f"MQTT RDDL connect")
            await self.client.connect(
                config.rddl.mqtt.host, config.rddl.mqtt.port, keepalive=60, version=MQTTv311, ssl=True
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
            elif self.challengee != "" and topic == "stat/" + self.challengee + "/POPCHALLENGERESULT":
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
        (initiator, challenger, challengee, pop_height, isChallenger, valid) = await queryPoPInfo(data)
        logger.info(
            "PoP context: challenger: "
            + challenger
            + " challengee: "
            + challengee
            + " pop_height: "
            + str(pop_height)
            + " valid pop request: "
            + str(valid)
            + " is challenger: "
            + str(isChallenger)
        )

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
        logger.info("PoP challenge cid data : " + cid_data)
        cid_data_hex = utils.toHexString(cid_data)
        logger.info("PoP challenge cid data hex : " + cid_data_hex)

        payload = '{ "PoPChallenge": { "cid": "' + cid + '", "encoding": "hex", "data": "' + cid_data_hex + '"} }'
        topic = "stat/" + self.challengee + "/POPCHALLENGERESULT"
        msg = Message(
            topic,
            payload,
            qos=1,
            content_type="json",
            message_expiry_interval=60,
            user_property=("time", str(datetime.now())),
        )
        self.client.publish(msg)
        self.clear_pop_context()
        return

    async def sendPoPResult(self, success: bool):
        keys = trust_wallet_instance.get_planetmint_keys()
        accountID, sequence, status = getAccountInfo(config.rddl.planetmint_api, keys.planetmint_address)
        if status != "":
            logger.error(f"error: {status}, message: {status}")
        txMsg = getPoPResultTx(
            self.challengee, self.initiator, self.pop_height, success, config.rddl.chain_id, accountID, sequence
        )
        response = broadcastTX(txMsg, config.rddl.planetmint_api)
        if response.status_code != 200:
            logger.error(f"error: {response.reason,}, message: {response.text}")

    async def pop_challenge_result(self, data):
        logger.info("PoP challenge result: " + data)
        self.client.unsubscribe("stat/" + self.challengee + "/POPCHALLENGERESULT")
        try:
            jsonObj = json.loads(data)
            if not jsonObj["PoPChallenge"]:
                logger.error('RDDL MQTT PoP Result: wrong JSON object. expected "PoPChallenge" got ' + data)
                asyncio.create_task(self.sendPoPResult(False))
            elif self.cid != jsonObj["PoPChallenge"]["cid"]:
                logger.error(
                    "RDDL MQTT PoP Result: wrong cid. expected " + self.cid + " got " + jsonObj["PoPChallenge"]["cid"]
                )
                asyncio.create_task(self.sendPoPResult(False))
            elif "hex" != jsonObj["PoPChallenge"]["encoding"]:
                logger.error("RDDL MQTT PoP Result: unsupported encoding.")
                asyncio.create_task(self.sendPoPResult(False))
            else:
                cid_data_encoded = jsonObj["PoPChallenge"]["data"]
                cid_data = utils.fromHexString(cid_data_encoded)
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
        cids = await queryNotatizedAssets(challengee, 20)
        if not cids or len(cids) == 0:
            logger.error("RDDL MQTT init PoP could not retrieve cids.")
            asyncio.create_task(self.sendPoPResult(False))
            return

        random_cid = random.choice(cids)
        self.cid = random_cid
        self.client.subscribe("stat/" + challengee + "/POPCHALLENGERESULT")
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
                asyncio.create_task(self.postStatus(keys.planetmint_address))
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
