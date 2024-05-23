import logging
from fastapi import APIRouter, HTTPException, Body
import netifaces
from scapy.all import ARP, Ether, srp
import requests
from requests.auth import HTTPDigestAuth

from app.dependencies import config

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/smd",
    tags=["smd"],
    responses={404: {"detail": "Not found"}},
)


def get_ip_address():
    try:
        gateway_info = netifaces.gateways()
        default_interface = gateway_info["default"][netifaces.AF_INET][1]
        addresses = netifaces.ifaddresses(default_interface)
        if netifaces.AF_INET in addresses:
            ipv4_info = addresses[netifaces.AF_INET][0]
            ip_address = ipv4_info["addr"]
            return ip_address
    except Exception as e:
        logger.error(f"Error getting IP address: {e}")
    return None


def get_ip_range():
    ip_address = get_ip_address()
    if not ip_address:
        return None
    base_ip = ".".join(ip_address.split(".")[:-1]) + ".0"
    ip_network = f"{base_ip}/24"
    return ip_network


def scan_network(ip_range):
    arp = ARP(pdst=ip_range)
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = ether / arp
    try:
        result = srp(packet, timeout=120, verbose=0)[0]
    except Exception as e:
        logger.error(f"Error scanning network: {e}")
        return []
    devices = [{"ip": received.psrc, "mac": received.hwsrc} for sent, received in result]
    return devices


def identify_shelly(ip_address):
    try:
        response = requests.get(f"http://{ip_address}/shelly", timeout=3)
        if response.ok:
            status_data = response.json()
            device_name = status_data.get("id", f"Unknown Shelly Device (ID: {status_data.get('id', 'Unknown')})")
            return {"ip": ip_address, "name": device_name}
    except requests.RequestException as e:
        logger.error(f"Error identifying Shelly device at {ip_address}: {e}")
    return None


def identify_tasmota(ip_address):
    try:
        response = requests.get(f"http://{ip_address}/cm?cmnd=status", timeout=3)
        if response.ok:
            status_data = response.json()
            device_name = status_data.get("Status", {}).get("DeviceName", "Unknown Tasmota Device")
            return {"ip": ip_address, "name": device_name}
    except requests.RequestException as e:
        logger.error(f"Error identifying Tasmota device at {ip_address}: {e}")
    return None


@router.get("/scan-devices")
def scan_and_identify_devices():
    ip_range = get_ip_range()
    if not ip_range:
        raise HTTPException(status_code=500, detail="Could not determine IP range.")

    logger.info(f"Scanning network range: {ip_range}")
    devices = scan_network(ip_range)
    shelly_devices = []
    tasmota_devices = []
    for device in devices:
        ip = device["ip"]
        shelly = identify_shelly(ip)
        if shelly:
            shelly_devices.append(shelly)
        else:
            tasmota = identify_tasmota(ip)
            if tasmota:
                tasmota_devices.append(tasmota)

    return {
        "shelly_devices": shelly_devices,
        "tasmota_devices": tasmota_devices,
    }


def configure_shelly_mqtt(device_ip, mqtt_host, mqtt_port, mqtt_user, mqtt_password, custom_topic):
    config_url = f"http://{device_ip}/rpc/MQTT.SetConfig"
    reboot_url = f"http://{device_ip}/rpc"
    payload = {
        "config": {
            "enable": True,
            "server": f"{mqtt_host}:{mqtt_port}",
            "user": mqtt_user,
            "pass": mqtt_password,
            "clean_session": True,
            "qos": 0,
            "keep_alive": 60,
            "status_ntf": True,
            "rpc_ntf": False,
            "topic_prefix": custom_topic,
        }
    }

    logger.info(f"Configuring MQTT on Shelly device at {device_ip} with payload: {payload}")

    try:
        response = requests.post(config_url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info(f"Successfully configured MQTT on Shelly device {device_ip}: {response.json()}")

        # Reboot the device to apply the new configuration
        reboot_payload = {"id": 1, "method": "Shelly.Reboot"}
        reboot_response = requests.post(reboot_url, json=reboot_payload, timeout=10)
        reboot_response.raise_for_status()
        logger.info(f"Successfully rebooted Shelly device {device_ip}")
    except requests.RequestException as e:
        logger.error(f"Error configuring MQTT on Shelly device {device_ip}: {e}, Response: {response.text}")
        raise HTTPException(status_code=500, detail=f"Error configuring MQTT on Shelly device {device_ip}: {e}")


def configure_tasmota_mqtt(device_ip, mqtt_host, mqtt_port, mqtt_user, mqtt_password, topic, telemetry_interval=60):
    base_url = f"http://{device_ip}/cm"
    try:
        requests.get(f"{base_url}?cmnd=MqttHost {mqtt_host}")
        requests.get(f"{base_url}?cmnd=MqttPort {mqtt_port}")
        requests.get(f"{base_url}?cmnd=MqttUser {mqtt_user}")
        requests.get(f"{base_url}?cmnd=MqttPassword {mqtt_password}")
        requests.get(f"{base_url}?cmnd=FullTopic {topic}")
        requests.get(f"{base_url}?cmnd=TelePeriod {telemetry_interval}")
    except requests.RequestException as e:
        logger.error(f"Error configuring MQTT on Tasmota device {device_ip}: {e}")
        raise HTTPException(status_code=500, detail=f"Error configuring MQTT on Tasmota device {device_ip}: {e}")


@router.post("/configure-device")
def configure_device(
    device_type: str = Body(...),
    device_ip: str = Body(...),
    device_name: str = Body(...),
    mqtt_host: str = Body(...),
    mqtt_port: int = Body(...),
    mqtt_user: str = Body(...),
    mqtt_password: str = Body(...),
    telemetry_interval: int = Body(default=60),
):
    custom_topic = build_mqtt_topic(remove_hashtag_from_topic(config.rddl_topic), device_name)
    if device_type.lower() == "shelly":
        logger.info(f"Configuring Shelly device at {device_ip}")
        configure_shelly_mqtt(
            device_ip, mqtt_host, mqtt_port, mqtt_user, mqtt_password, custom_topic
        )
    elif device_type.lower() == "tasmota":
        configure_tasmota_mqtt(
            device_ip, mqtt_host, mqtt_port, mqtt_user, mqtt_password, custom_topic, telemetry_interval
        )
    else:
        raise HTTPException(status_code=400, detail="Unsupported device type")
    return {"detail": f"{device_type} device at {device_ip} configured successfully."}


def remove_hashtag_from_topic(topic):
    return topic.replace("#", "")


def build_mqtt_topic(base_topic, device_name):
    if base_topic.endswith('/'):
        base_topic = base_topic[:-1]

    if device_name.startswith('/'):
        device_name = device_name[1:]

    mqtt_topic = f"{base_topic}/{device_name}"

    return mqtt_topic


@router.get("/ip-address")
def get_ip_address_route():
    return {"ip": get_ip_address()}
