import json
from datetime import datetime
import requests
import asyncio
import random
import binascii
from gmqtt import Client as MQTTClient
from gmqtt import Message
from gmqtt.mqtt.constants import MQTTv311
from typing import Tuple, List

from app.RddlInteraction.cid_tool import store_cid
from app.RddlInteraction.planetmint_interaction import create_tx_notarize_data
from app.dependencies import config, logger
from app.energy_agent.energy_decrypter import decrypt_device
from app.helpers.config_helper import load_config
from app.helpers.models import MQTTConfig
from app.dependencies import trust_wallet_instance
from app.db.cid_store import get_value
from app.RddlInteraction.cid_tool import compute_cid


class RDDLAgent:
    def __init__(self):
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
            self.initialize_mqtt_client()
        except Exception as e:
            logger.error(f"MQTT RDDL Setup error: {e}")
            raise

    def initialize_mqtt_client(self):
        keys = trust_wallet_instance.get_planetmint_keys()
        self.client = MQTTClient(client_id=keys.planetmint_address)
        self.client.on_message = self.on_message
        self.client.set_auth_credentials(self.mqtt_config.mqtt_username, self.mqtt_config.mqtt_password)

    async def connect_to_mqtt(self):
        try:
            await self.client.connect(
                self.mqtt_config.mqtt_host, self.mqtt_config.mqtt_port, keepalive=60, version=MQTTv311, ssl=True
            )
        except Exception as e:
            logger.error(f"MQTT RDDL connection error: {e}")
            raise

    async def disconnect_from_mqtt(self):
        try:
            await self.client.disconnect()
        except Exception as e:
            logger.error(f"MQTT RDDL disconnection error: {e}")

    async def on_message(self, client, topic, payload, qos, properties):
        try:
            decoded_payload = payload.decode()
            self.process_message(topic, decoded_payload)
            logger.info(f"MQTT RDDL Received message: {topic}, {decoded_payload}")
        except UnicodeDecodeError:
            logger.error("MQTT RDDL Error decoding the message payload")
        except Exception as e:
            logger.error(f"MQTT RDDL Unexpected error processing message: {e}")

    def process_message(self, topic, data):
        keys = trust_wallet_instance.get_planetmint_keys()
        if topic == "cmnd/" + keys.planetmint_address + "/PoPChallenge":
            asyncio.create_task(self.pop_challenge(data))
        elif topic == "cmnd/" + keys.planetmint_address + "/PoPInit":
            asyncio.create_task(self.pop_init(data))
        elif self.challengee != "" and topic == "cmnd/" + self.challengee + "/PoPChallengeResult":
            asyncio.create_task(self.pop_challenge_result(data))
        else:
            logger.debug(f"MQTT RDDL topic currently not supported: " + topic)

    def clear_pop_participants(self):
        self.challengee = ""
        self.challenger = ""
        self.cid = ""

    async def pop_init(self, data):
        logger.info("PoP init: " + data)
        (challenger, challengee, isChallenger, valid) = await self.queryPoPInfo(data)
        logger.info("challenger : " + challenger)
        logger.info("challengee : " + challengee)
        logger.info("valid : " + str(valid))
        if valid:
            self.challenger = challenger
            self.challengee = challengee
            if isChallenger:
                asyncio.create_task(self.initPoPChallenge(challengee))
                return
            else:
                # wait for PoP challenge
                return


    def toHexString(self, data: str) -> str:        
        hexBytes = binascii.hexlify(data.encode('utf-8'))
        hexString =  hexBytes.decode('utf-8')
        return hexString
    
    def fromHexString(self, hexString: str) -> str:
        dataString = binascii.unhexlify(hexString.encode('utf-8')).decode('utf-8')
        return dataString

    async def pop_challenge(self, data: str):
        logger.info("PoP challenge : " + data)
        if self.challengee != trust_wallet_instance.get_planetmint_keys().planetmint_address:
            return
        cid = data
        cid_data = get_value(cid)
        cid_data_hex = self.toHexString(cid_data)
        topic = "cmnd/" + self.challengee + "/PoPChallengeResult"
        payload = '{ "PoPChallengeResult": \{ "cid": "' + cid + '", "encoding": "hex", "data": "' + cid_data_hex + '"} }'
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
        # TODO integrate
        return

    async def pop_challenge_result(self, data):
        logger.info("PoP challenge result: " + data)
        self.client.unsubscribe("stat/" + self.challengee + "/PoPChallengeResult")
        try:
            jsonObj = json.loads(data)
            jsonObj["PoPChallengeResult"]["data"]
            if self.cid != jsonObj["PoPChallengeResult"]["cid"]:
                logger.error("RDDL MQTT PoP Result: wrong cid. expected " + self.cid + " got " + jsonObj["PoPChallengeResult"]["cid"])
                asyncio.create_task(self.sendPoPResult(False))
            elif "hex" != jsonObj["PoPChallengeResult"]["encoding"]:
                logger.error("RDDL MQTT PoP Result: unsupported encoding.")
                asyncio.create_task(self.sendPoPResult(False))
            else:
                cid_data_encoded = jsonObj["PoPChallengeResult"]["data"]
                cid_data = self.fromHexString( cid_data_encoded)
                computed_cid = compute_cid(cid_data)
                if computed_cid == self.cid:
                    asyncio.create_task(self.sendPoPResult(True))
                else:
                    asyncio.create_task(self.sendPoPResult(False))
        except json.JSONDecodeError:
            logger.error("RDDL MQTT PoP Result: Error: Invalid JSON string.")
            asyncio.create_task(self.sendPoPResult(False))

    async def initPoPChallenge(self, challengee: str):
        cids = await self.queryNotatizedAssets(challengee, 20)
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

    async def queryPoPInfo(self, height) -> Tuple[str, str, bool, bool]:
        # Define the API endpoint URL
        url = config.planetmint_api + "/planetmint/dao/challenge/" + height
        # Set the header for accepting JSON data
        headers = {"accept": "application/json"}

        # Send a GET request using requests library
        response = requests.get(url, headers=headers)

        # Check for successful response status code
        if response.status_code == 200:
            # Parse the JSON response (assuming successful status code)
            try:
                data = json.loads(response.text)

                # Verify "challenge" key exists and all desired keys are present
                if "challenge" in data and all(
                    key in data["challenge"]
                    for key in ["initiator", "challenger", "challengee", "height", "success", "finished"]
                ):
                    # Access and print the challenge variables
                    logger.info("Initiator: " + data["challenge"]["initiator"])
                    logger.info("Challenger: " + data["challenge"]["challenger"])
                    logger.info("Challengee: " + data["challenge"]["challengee"])
                    logger.info("Height: " + data["challenge"]["height"])
                    logger.info("Success: " + str(data["challenge"]["success"]))
                    logger.info("Finished: " + str(data["challenge"]["finished"]))
                    if (
                        data["challenge"]["height"] == height
                        and data["challenge"]["success"] == False
                        and data["challenge"]["finished"] == False
                    ):

                        keys = keys = trust_wallet_instance.get_planetmint_keys()
                        challenger = data["challenge"]["challenger"]
                        challengee = data["challenge"]["challengee"]
                        isChallenger = challenger == keys.planetmint_address
                        if isChallenger or challengee == keys.planetmint_address:
                            return (challenger, challengee, isChallenger, True)
                else:
                    logger.error("Error: Missing key(s) in response.")
            except json.JSONDecodeError:
                logger.error("Error: Invalid JSON response.")
        else:
            logger.error("Error:", response.status_code)
        return ("", "", False, False)

    async def queryNotatizedAssets(self, challengee: str, num_cids: int) -> List[str]:
        # Define the API endpoint URL
        url = config.planetmint_api + "/planetmint/dao/challenge/" + challengee + "/" + str(num_cids)
        # Set the header for accepting JSON data
        headers = {"accept": "application/json"}

        # Send a GET request using requests library
        response = requests.get(url, headers=headers)

        # Check for successful response status code
        if response.status_code == 200:
            # Parse the JSON response (assuming successful status code)
            try:
                data = json.loads(response.text)

                # Verify "challenge" key exists and all desired keys are present
                if "cids" in data:
                    return data["cids"]
                else:
                    logger.error("Error: Missing key(s) in response.")
            except json.JSONDecodeError:
                logger.error("Error: Invalid JSON response.")
        else:
            logger.error("Error:", response.status_code)
        return None

    async def run(self):
        try:
            await self.connect_to_mqtt()
            keys = trust_wallet_instance.get_planetmint_keys()

            self.client.subscribe("cmnd/" + keys.planetmint_address + "/PoPChallenge")
            self.client.subscribe("cmnd/" + keys.planetmint_address + "/PoPInit")

            self.client.subscribe(config.rddl_topic)

            while not self.stopped:
                await self.postStatus(keys.planetmint_address)
                await asyncio.sleep(60)

        except Exception as e:
            logger.error(f"MQTT RDDL Error in RDDLAgent run loop: {e}")
        finally:
            await self.disconnect_from_mqtt()

    async def postStatus(self, address: str):
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
