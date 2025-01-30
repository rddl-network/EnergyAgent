import pytest
from app.dependencies import config, PRODUCTION_READOUT_MODE_CERBOGX, measurement_instance
from app.energy_agent.cerbogx import process_production_readout


def test_cerbogx_value_extraction():
    config.production_readout_mode = PRODUCTION_READOUT_MODE_CERBOGX
    topic = "N/c0619ab2c15d/system/0/Dc/Pv/Power"

    # string
    data = "2450.0"
    process_production_readout(topic, data)
    assert 2.45 == measurement_instance.production

    # float
    data = 2450.0
    process_production_readout(topic, data)
    assert 2.45 == measurement_instance.production

    # int
    data = 2450
    process_production_readout(topic, data)
    assert 2.45 == measurement_instance.production
