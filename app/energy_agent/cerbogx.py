import re
from app.dependencies import PRODUCTION_READOUT_MODE_CERBOGX, config, measurement_instance
from app.model.measurements import Measurements


def process_production_readout(topic: str, data: str):
    if config.production_readout_mode != PRODUCTION_READOUT_MODE_CERBOGX:
        return
    if re.match(config.production_readout_pattern, topic):
        kwh_production = float(data)
        measurement_instance.set_abs_production_value(kwh_production)
