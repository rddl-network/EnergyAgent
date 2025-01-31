import pytest
from app.model.measurements import Measurements


def test_overall_production_computation():
    measurements = Measurements()

    measurements.set_abs_production_value(1.0, "a")
    measurements.set_abs_production_value(1.5, "b")
    measurements.set_abs_production_value(1.0, "c")
    measurements.set_abs_production_value(1.5, "")
    measurements.set_abs_production_value(1.5, "d")

    assert 6.5 == measurements.get_overall_production()


def test_overall_production_compution_with_overwrite():
    measurements = Measurements()

    measurements.set_abs_production_value(1.0, "a")
    measurements.set_abs_production_value(1.5, "b")
    measurements.set_abs_production_value(1.0, "b")

    assert 2.0 == measurements.get_overall_production()
