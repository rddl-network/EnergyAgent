import pytest
from app.energy_agent.shellypro3em import get_production_value_in_wh, get_production_value_in_kwh


raw_data = '{"id":0,"a_total_act_energy":39922.93,"a_total_act_ret_energy":1075.97,"b_total_act_energy":39898.66,"b_total_act_ret_energy":484.19,"c_total_act_energy":40056.66,"c_total_act_ret_energy":46.89,"total_act":119878.25, "total_act_ret":1607.05}'


def test_shellypro3em_value_extraction():
    wh_production = get_production_value_in_wh(raw_data)
    assert 119878.25 == wh_production

    kwh_production = get_production_value_in_kwh(raw_data)
    assert 119.87825 == kwh_production
