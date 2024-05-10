import netifaces
from scapy.all import ARP, Ether, srp
import requests

# Get the network IP range dynamically
def get_ip_range():
    try:
        # Get the default gateway
        gateway_info = netifaces.gateways()
        default_interface = gateway_info['default'][netifaces.AF_INET][1]

        # Get the IP address of the default interface
        addresses = netifaces.ifaddresses(default_interface)
        if netifaces.AF_INET in addresses:
            ipv4_info = addresses[netifaces.AF_INET][0]
            ip_address = ipv4_info['addr']

            # Replace the last part of the IP address with `0` and use a /24 subnet mask
            base_ip = ".".join(ip_address.split(".")[:-1]) + ".0"
            ip_network = f"{base_ip}/24"
            return ip_network
    except KeyError:
        pass
    return None


# Scan the network for devices
def scan_network(ip_range):
    arp = ARP(pdst=ip_range)
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = ether / arp
    result = srp(packet, timeout=30, verbose=0)[0]
    devices = [{"ip": received.psrc, "mac": received.hwsrc} for sent, received in result]
    return devices


# Identify and return information about a Shelly device, including its name
def identify_shelly(ip_address):
    try:
        response = requests.get(f"http://{ip_address}/status", timeout=3)
        if "shelly" in response.text.lower():
            status_data = response.json()
            device_name = status_data.get("device", {}).get("name", "Unknown Shelly Device")
            return {"ip": ip_address, "name": device_name}
    except requests.RequestException:
        pass
    return None


# Identify and return information about a Tasmota device, including its name
def identify_tasmota(ip_address):
    try:
        response = requests.get(f"http://{ip_address}/cm?cmnd=status", timeout=3)
        if response.ok:
            status_data = response.json()
            device_name = status_data.get("Status", {}).get("DeviceName", "Unknown Tasmota Device")
            return {"ip": ip_address, "name": device_name}
    except requests.RequestException:
        pass
    return None


# Find all Shelly devices on the network
def find_shelly_devices(network_devices):
    return [identify_shelly(device["ip"]) for device in network_devices if identify_shelly(device["ip"])]


# Find all Tasmota devices on the network
def find_tasmota_devices(network_devices):
    return [identify_tasmota(device["ip"]) for device in network_devices if identify_tasmota(device["ip"])]


# Get the IP range dynamically
ip_range = get_ip_range()
print("IP Range:", ip_range)

if ip_range:
    devices = scan_network(ip_range)
    print("Devices on network:", devices)
    shelly_devices = find_shelly_devices(devices)
    tasmota_devices = find_tasmota_devices(devices)
    print("Identified Shelly Devices:", shelly_devices)
    print("Identified Tasmota Devices:", tasmota_devices)
else:
    print("Could not determine IP range.")
