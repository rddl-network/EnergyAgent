import grpc
import json
import time
import paho.mqtt.client as mqtt

from app.dependencies import config, logger
from app.energy_meter_interaction.energy_decrypter import (
    extract_data,
    decode_packet,
    decrypt_evn_data,
    transform_to_metrics,
    decrypt_aes_gcm_landis_and_gyr,
    decrypt_sagemcom,
)
from app.proto.MeterConnectorProto import meter_connector_pb2_grpc, meter_connector_pb2
from submoudles.submodules.app_mypower_modul.schemas import MetricCreate
import concurrent.futures

SM_READ_ERROR = "ERROR! SM METER READ"
DEFAULT_SLEEP_TIME = 5


class DataFetcher:
    def __init__(self):
        self.mqtt_client = None
        self.stopped = False

        self.connect_to_mqtt()

    def fetch_data(self):
        logger.info("start fetching")
        while not self.stopped:
            try:
                logger.info("Starting a new fetch cycle")
                time.sleep(DEFAULT_SLEEP_TIME)

                logger.info("Sending request to Smart Meter")
                response = self.get_meter_response_with_timeout(config.smart_meter_timeout)

                if response is None or response.message == SM_READ_ERROR:
                    logger.error(f"No data from Smart Meter: {response}")
                    continue

                data_hex = response.message
                logger.debug(f"data_hex: {data_hex}")
                metric = self.decrypt_device(data_hex)
                self.post_to_mqtt(metric)

                time.sleep(config.interval)
            except UnicodeDecodeError as e:
                logger.error(f"Invalid Frame: {e}")
                continue
            except ValueError as e:
                logger.error(f"Invalid Frame: {e}")
                continue
            except concurrent.futures.TimeoutError:
                logger.info("The function call timed out.")
                continue
            except Exception as e:
                logger.error(f"DataFetcher thread failed with exception: {e}")
                exit(1)

    @staticmethod
    def get_meter_response_with_timeout(timeout=10):
        def make_grpc_call():
            with grpc.insecure_channel(config.grpc_endpoint) as channel:
                stub = meter_connector_pb2_grpc.MeterConnectorStub(channel)
                request = meter_connector_pb2.SMDataRequest()
                return stub.readMeter(request)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(make_grpc_call)
            try:
                response = future.result(timeout=timeout)
                return response
            except concurrent.futures.TimeoutError:
                logger.info("The function call timed out.")
                raise TimeoutError("The function call timed out.")
                return None

    @staticmethod
    def decrypt_device(data_hex):
        if config.device == "EVN":
            dec = decrypt_evn_data(data_hex)
            return transform_to_metrics(dec, config.pubkey)
        elif config.device == "LG":
            dec = decrypt_aes_gcm_landis_and_gyr(
                data_hex, bytes.fromhex(config.encryption_key), bytes.fromhex(config.authentication_key)
            )
            return transform_to_metrics(dec, config.pubkey)
        elif config.device == "SC":
            dec = decrypt_sagemcom(
                data_hex, bytes.fromhex(config.encryption_key), bytes.fromhex(config.authentication_key)
            )
            return transform_to_metrics(dec, config.pubkey)
        else:
            decoded_packet = decode_packet(bytearray.fromhex(data_hex))
            metric = extract_data(decoded_packet)
            if metric is None:
                logger.error("data is None")
                raise ValueError("data is None")
            return metric

    def post_to_mqtt(self, data: MetricCreate):
        logger.info("Posting to MQTT")

        metric_dict = data.dict()
        metric_dict["time_stamp"] = metric_dict["time_stamp"].isoformat()
        metric_dict["absolute_energy_in"] = float(metric_dict["absolute_energy_in"])
        metric_dict["absolute_energy_out"] = float(metric_dict["absolute_energy_out"])
        logger.debug(f"Metric data: {metric_dict}")

        message = json.dumps(metric_dict)
        try:
            result = self.mqtt_client.publish(config.mqtt_topic, payload=message, qos=1)
            result.wait_for_publish()
            logger.info(f" [x] Sent {message}")
        except Exception as e:
            logger.error(f"Exception occurred while publishing to MQTT: {e}")
            self.handle_publish_failure(data)

    def connect_to_mqtt(self):
        self.mqtt_client = mqtt.Client(client_id=config.pubkey, protocol=mqtt.MQTTv311)
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_disconnect = self.on_disconnect
        self.mqtt_client.on_publish = self.on_publish
        self.mqtt_client.username_pw_set(config.mqtt_username, config.mqtt_password)
        try:
            self.mqtt_client.connect(config.mqtt_host, config.mqtt_port, 60)
            self.mqtt_client.loop_start()  # Start the network loop
        except Exception as e:
            logger.error(f"Exception occurred while connecting to MQTT: {e}")

    def handle_publish_failure(self, data):
        logger.warning("Attempting to republish to MQTT")
        try:
            self.mqtt_client.reconnect()  # Attempt to reconnect
            self.post_to_mqtt(data)  # Try to republish the data
        except Exception as e:
            logger.error(f"Republishing failed: {e}")

    def on_connect(self, client, userdata, flags, rc):
        logger.info(f"Connected to MQTT Broker with result code {rc}")

    def on_disconnect(self, client, userdata, rc):
        logger.info("Disconnected from MQTT Broker")

    def on_publish(self, client, userdata, mid):
        logger.info(f"Message with mid {mid} has been published.")
