import re
import xml.etree.ElementTree as ET

from app.helpers.api_helper import fetch_xml


def extract_wr_energy_values(xml_content: str) -> dict:
    """
    Extract WR energy values from SmartFox XML output.
    Returns dict with wrXEnergyValue as keys and values in kWh as float.
    """
    root = ET.fromstring(xml_content)
    wr_values = {}

    for i in range(1, 6):
        key = f"wr{i}EnergyValue"
        value = root.find(f'.//value[@id="{key}"]')
        if value is not None:
            # Extract numeric value and convert to float
            kwh = float(re.search(r"([\d.]+)", value.text).group(1))
            wr_values[key] = kwh

    return wr_values


def get_produced_energy(xml_content: str) -> float:
    values = extract_wr_energy_values(xml_content)
    production = 0
    for key in values:
        production = production + values[key]
    return production


async def fetch_smartfox_values(ip: str, path="values.xml", protocol="http"):
    url = f"{protocol}://{ip}/{path}"
    xml_content = await fetch_xml(url)
    return xml_content


async def get_smartfox_energy_production(ip: str) -> float:
    xml_content = await fetch_smartfox_values(ip)
    produced_energy = await get_produced_energy(xml_content)
    return produced_energy
