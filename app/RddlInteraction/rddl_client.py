import json
from datetime import datetime
import asyncio
import random

from gmqtt import Client as MQTTClient
from gmqtt import Message
from gmqtt.mqtt.constants import MQTTv311

from app.dependencies import config, trust_wallet_instance
from app.db.activity_store import insert_tx_activity_by_response, insert_mqtt_activity
from app.db.cid_store import get_value
from app.helpers.models import PoPContext
from app.RddlInteraction import utils
from app.RddlInteraction.cid_tool import compute_cid
from app.RddlInteraction.api_queries import queryPoPInfo, getAccountInfo, queryNotatizedAssets
from app.RddlInteraction.planetmint_interaction import broadcastTX, getPoPResultTx
from app.helpers.logs import log, logger


class RDDLAgent:
    def __init__(self):
        logger.info("MQTT RDDL creation")

        # client management
        self.client = None
        self.stopped = False
        self.pop_context = PoPContext()
        self.lock = asyncio.Lock()

    @log
    def setup(self):
        try:
            logger.info("MQTT RDDL setup")
            keys = trust_wallet_instance.get_planetmint_keys()
            self.client = MQTTClient(client_id=keys.planetmint_address)
            self.client.on_message = self.on_message
            self.client.set_auth_credentials(config.rddl.mqtt.username, config.rddl.mqtt.password)
        except Exception as e:
            logger.error(f"MQTT RDDL Setup error: {e}")
            raise

    @log
    async def connect_to_mqtt(self):
        try:
            logger.info("MQTT RDDL connect")
            await self.client.connect(
                config.rddl.mqtt.host, config.rddl.mqtt.port, keepalive=60, version=MQTTv311, ssl=True
            )
        except Exception as e:
            logger.error(f"MQTT RDDL connection error: {e}")
            raise

    @log
    async def disconnect_from_mqtt(self):
        try:
            logger.info("MQTT RDDL disconnection")
            await self.client.disconnect()
        except Exception as e:
            logger.error(f"MQTT RDDL disconnection error: {e}")

    @log
    def on_message(self, client, topic, payload, qos, properties):
        asyncio.create_task(self.process_message(client, topic, payload, qos, properties))

    async def setContext(self, context: PoPContext):
        async with self.lock:
            self.pop_context = context

    async def getContext(self) -> PoPContext:
        async with self.lock:
            pop_context = self.pop_context
            return pop_context

    @log
    async def process_message(self, client, topic, payload, qos, properties):
        pop_context = await self.getContext()
        try:
            decoded_payload = payload.decode()
            logger.info(f"MQTT RDDL Received message: {topic}, {decoded_payload}")
            keys = trust_wallet_instance.get_planetmint_keys()
            if topic == "cmnd/" + keys.planetmint_address + "/PoPChallenge":
                asyncio.create_task(self.challengee_pop_challenge(decoded_payload))
            elif topic == "cmnd/" + keys.planetmint_address + "/PoPInit":
                asyncio.create_task(self.pop_init(decoded_payload))
            elif pop_context.challengee != "" and topic == "stat/" + pop_context.challengee + "/POPCHALLENGERESULT":
                asyncio.create_task(self.challenger_2_consume_pop_challenge_response(decoded_payload))
            else:
                logger.debug("MQTT RDDL topic currently not supported: " + topic)
        except UnicodeDecodeError:
            logger.error("MQTT RDDL Error decoding the message payload")
        except Exception as e:
            logger.error(f"MQTT RDDL Unexpected error processing message: {e}")

    @log
    async def watchdog_cancel_pop_request(self, pop_height: int):
        await asyncio.sleep(80)
        pop_context = await self.getContext()
        if pop_height != pop_context.pop_height:
            return
        if not pop_context.isActive:
            await self.setContext(PoPContext)
            return

        logger.info("PoP Watchdog is terminating the current PoP: " + str(pop_context.pop_height))
        isChallenger = pop_context.isChallenger
        if isChallenger:
            await self.challenger_3_sendPoPResult(False, pop_height)
        else:
            await self.setContext(PoPContext)

    @log
    async def pop_init(self, data):
        logger.info("PoP init: " + data)
        pop_context = await queryPoPInfo(data)
        logger.info(
            "PoP context: challenger: "
            + pop_context.challenger
            + " challengee: "
            + pop_context.challengee
            + " pop_height: "
            + str(pop_context.pop_height)
            + " valid pop request: "
            + str(pop_context.isActive)
            + " is challenger: "
            + str(pop_context.isChallenger)
        )
        if pop_context.isActive:
            await self.setContext(pop_context)
            insert_mqtt_activity("PoPInit " + data, "initialized", pop_context.__dict__)
            if pop_context.isChallenger:
                # init PoP
                asyncio.create_task(self.challenger_1_initPoPChallenge(pop_context.challengee))
                # cancel PoP if challengee did not respond to the challenge
                asyncio.create_task(self.watchdog_cancel_pop_request(pop_context.pop_height))
                return
            else:
                # wait for PoP challenge
                # cancel PoP if challenger did not send out challenge
                asyncio.create_task(self.watchdog_cancel_pop_request(pop_context.pop_height))
                return

    @log
    async def challengee_pop_challenge(self, data: str):
        pop_context = await self.getContext()
        logger.info("PoP challenge : " + data)
        if pop_context.challengee != trust_wallet_instance.get_planetmint_keys().planetmint_address:
            return
        insert_mqtt_activity("PoPChallenge " + data, "receive PoPChallenge", pop_context.__dict__)
        cid = data
        cid_data = get_value(cid)
        logger.info(f"PoP challenge cid data : {cid_data}")
        cid_data_hex = utils.toHexString(json.dumps(cid_data))
        logger.info(f"PoP challenge cid data hex : {cid_data_hex}")

        payload = '{ "PoPChallenge": { "cid": "' + cid + '", "encoding": "hex", "data": "' + cid_data_hex + '"} }'
        topic = "stat/" + pop_context.challengee + "/POPCHALLENGERESULT"
        msg = Message(
            topic,
            payload,
            qos=1,
            content_type="json",
            message_expiry_interval=60,
            user_property=("time", str(datetime.now())),
        )
        self.client.publish(msg)
        insert_mqtt_activity("PoPChallengeResult", "send", payload)
        await self.setContext(pop_context)
        return

    @log
    async def challenger_1_initPoPChallenge(self, challengee: str):
        logger.info("RDDL MQTT init PoP")
        cids = await queryNotatizedAssets(challengee, 20)
        pop_context = await self.getContext()
        if not cids or len(cids) == 0:
            logger.error("RDDL MQTT init PoP could not retrieve cids.")
            insert_mqtt_activity("PoPChallenge", "no CIDS", "challengee cCID query failed")
            await asyncio.create_task(self.challenger_3_sendPoPResult(False, pop_context.pop_height))
            return

        random_cid = random.choice(cids)
        pop_context.cid = random_cid
        await self.setContext(pop_context)
        insert_mqtt_activity("PoPChallenge", "send", "CID challenged " + random_cid)
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

    @log
    async def challenger_2_consume_pop_challenge_response(self, data):
        pop_context = await self.getContext()
        logger.info("PoP challenge result: " + data)
        self.client.unsubscribe("stat/" + pop_context.challengee + "/POPCHALLENGERESULT")
        try:
            jsonObj = json.loads(data)
            if not jsonObj["PoPChallenge"]:
                logger.error('RDDL MQTT PoP Result: wrong JSON object. expected "PoPChallenge" got ' + data)
                insert_mqtt_activity("PoPChallengeResult", "bad JSON object", "result: " + data)
                await asyncio.create_task(self.challenger_3_sendPoPResult(False, pop_context.pop_height))
            elif pop_context.cid != jsonObj["PoPChallenge"]["cid"]:
                logger.error(
                    "RDDL MQTT PoP Result: wrong cid. expected "
                    + pop_context.cid
                    + " got "
                    + jsonObj["PoPChallenge"]["cid"]
                )
                insert_mqtt_activity("PoPChallengeResult", "wrong CID", "result: " + data)
                await asyncio.create_task(self.challenger_3_sendPoPResult(False, pop_context.pop_height))
            elif "hex" != jsonObj["PoPChallenge"]["encoding"]:
                logger.error("RDDL MQTT PoP Result: unsupported encoding.")
                insert_mqtt_activity("PoPChallengeResult", "unsuppported encoding", "result: " + data)
                await asyncio.create_task(self.challenger_3_sendPoPResult(False, pop_context.pop_height))
            else:
                cid_data_encoded = jsonObj["PoPChallenge"]["data"]
                cid_data = utils.fromHexString(cid_data_encoded)
                computed_cid = compute_cid(cid_data)
                if computed_cid == pop_context.cid:
                    insert_mqtt_activity("PoPChallengeResult", "success", "result: " + data)
                    await asyncio.create_task(self.challenger_3_sendPoPResult(True, pop_context.pop_height))
                else:
                    insert_mqtt_activity("PoPChallengeResult", "CID verification failed", "result: " + data)
                    await asyncio.create_task(self.challenger_3_sendPoPResult(False, pop_context.pop_height))
        except json.JSONDecodeError:
            logger.error("RDDL MQTT PoP Result: Error: Invalid JSON string.")
            insert_mqtt_activity("PoPChallengeResult", "invalid JSON obj", "result: " + data)
            await asyncio.create_task(self.challenger_3_sendPoPResult(False, pop_context.pop_height))

    @log
    async def challenger_3_sendPoPResult(self, success: bool, pop_height: int):
        pop_context = await self.getContext()
        if not pop_context.isActive:
            return
        if pop_context.pop_height != pop_height:
            return

        keys = trust_wallet_instance.get_planetmint_keys()
        accountID, sequence, status = getAccountInfo(config.rddl.planetmint_api, keys.planetmint_address)
        if status != "":
            logger.error(f"error: {status}, message: {status}")
        txMsg = getPoPResultTx(
            pop_context.challengee,
            pop_context.initiator,
            pop_context.pop_height,
            success,
            config.rddl.chain_id,
            accountID,
            sequence,
        )
        response = broadcastTX(txMsg, config.rddl.planetmint_api)
        insert_tx_activity_by_response(response, "PoP result")
        if response.status_code != 200:
            logger.error(f"error: {response.reason,}, message: {response.text}")
        await self.setContext(PoPContext())

    @log
    async def run(self):
        logger.info("RDDL MQTT run.")
        try:
            await self.connect_to_mqtt()
            keys = trust_wallet_instance.get_planetmint_keys()

            self.client.subscribe("cmnd/" + keys.planetmint_address + "/PoPChallenge")
            self.client.subscribe("cmnd/" + keys.planetmint_address + "/PoPInit")

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
