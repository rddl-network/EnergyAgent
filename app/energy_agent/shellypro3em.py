import json

from app.dependencies import (
    config,
    measurement_instance,
    PRODUCTION_READOUT_MODE_SHELLYPRO3EM,
)
from app.helpers.api_helper import fetch_xml
from app.helpers.logs import logger
from app.model.measurements import Measurements


def get_production_value_in_wh(data: str) -> float:
    json_data = json.loads(data)
    total_production = json_data["total_act"]
    return total_production


def get_production_value_in_kwh(data: str) -> float:
    wh_production = get_production_value_in_wh(data)
    kwh_production = Measurements.convert_to_kwh(wh_production)
    return kwh_production


def fetch_shelly_pro_3em_values(ip: str, path="rpc/EMData.GetStatus?id=0", protocol="http"):
    url = f"{protocol}://{ip}/{path}"
    xml_content = fetch_xml(url)
    return xml_content


def get_shelly_pro_3em_energy_production(ip: str) -> float:
    json_content = fetch_shelly_pro_3em_values(ip)
    produced_energy = get_production_value_in_kwh(json_content)
    logger.debug(f"Production value: {produced_energy} ")
    return produced_energy


def read_shelly_pro_3em_values():
    if config.production_readout_mode != PRODUCTION_READOUT_MODE_SHELLYPRO3EM:
        return
    if config.production_readout_ip == "":
        return
    energy_production = get_shelly_pro_3em_energy_production(config.production_readout_ip)
    measurement_instance.set_abs_production_value(energy_production)
