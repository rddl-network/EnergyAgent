import pytest
from app.dependencies import config, PRODUCTION_READOUT_MODE_CERBOGX, measurement_instance
from app.energy_agent.cerbogx import process_production_readout


def test_cerbogx_value_extraction():
    config.production_readout_mode = PRODUCTION_READOUT_MODE_CERBOGX
    topic = "N/c0619ab2c15d/pvinverter/20/Ac/Energy/Forward"

    # float
    data = '{"value":443.842}'
    process_production_readout(topic, data)
    assert 443.842 == measurement_instance.get_overall_production()

    # int
    data = '{"value":443}'
    process_production_readout(topic, data)
    assert 443.0 == measurement_instance.get_overall_production()

    # string
    data = '{"value": "443.843"}'
    process_production_readout(topic, data)
    assert 443.843 == measurement_instance.get_overall_production()
