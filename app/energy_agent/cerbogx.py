import json
import re
from app.dependencies import PRODUCTION_READOUT_MODE_CERBOGX, config, measurement_instance
from app.helpers.logs import logger


def process_production_readout(topic: str, data: str):
    if config.production_readout_mode != PRODUCTION_READOUT_MODE_CERBOGX:
        return
    if re.match(config.production_readout_pattern, topic):        
        value_object = json.loads(data)
        kwh_production = float(value_object["value"])
        logger.info(f"Notarization: {kwh_production}, {topic}")
        measurement_instance.set_abs_production_value(kwh_production, topic)
